from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, FormView, View
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.db.models import Prefetch
from django.db import transaction
from django.utils.functional import cached_property
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import Bug, Action, Comment
from .forms import FilterForm, PresetFilterForm
from .mutation import BuggyBugMutator
from .enums import State

User = get_user_model()


class BugListView(LoginRequiredMixin, ListView):
    queryset = Bug.objects.select_related(
        'project', 'created_by', 'assigned_to'
    ).order_by(
        '-modified_at'
    )
    context_object_name = 'bugs'
    form_class = FilterForm

    def get_form_kwargs(self):
        return {
            'data': self.request.GET,
        }

    def get_form(self):
        return self.form_class(**self.get_form_kwargs())

    def get(self, *args, **kwargs):
        self.form = self.get_form()
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['preset_form'] = PresetFilterForm()
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        if self.form.is_valid():
            return self.form.filter(qs)
        else:
            return qs.none()


class BugMutationMixin(object):
    mutator_class = BuggyBugMutator

    @cached_property
    def state_machine(self):
        return self.mutator_class(self.request.user, self.object)

    def get_form_class(self):
        return self.state_machine.get_form_class()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = self.state_machine.get_actions()
        context['buggy_user_names'] = [
            user.get_short_name().lower() for user in User.objects.filter(is_active=True)
        ]
        context['buggy_open_bugs'] = [
            {
                'title': bug.title,
                'number': bug.number,
            } for bug in Bug.objects.exclude(state=State.CLOSED)
        ]
        return context

    def form_valid(self, form):
        try:
            action = self.state_machine.process_form(form)
        except ValidationError as e:
            for error in e.error_list:
                form.add_error(None, e)
            return self.form_invalid(form)
        else:
            return HttpResponseRedirect(action.bug.get_absolute_url())


class BugDetailView(LoginRequiredMixin, BugMutationMixin, FormView):
    template_name = 'buggy/bug_detail.html'

    queryset = Bug.objects.all().prefetch_related(
        Prefetch('actions', queryset=Action.objects.select_related(
            'user', 'comment', 'setpriority', 'setassignment__assigned_to',
            'setstate', 'setproject', 'settitle',
        ).prefetch_related('attachments'))
    ).select_related(
        'created_by', 'assigned_to', 'project'
    )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_object(self):
        try:
            if self.request.method == 'POST':
                # We'd like to just use select_for_update on the main queryset,
                # but the select_related does a left join. Postgres does not
                # support locking the outer side of an outer join. The SQL we
                # want is `SELECT ... FOR UPDATE OF buggy_bug`, which would
                # only lock the one table, but Django can't yet generate that
                # SQL: <https://code.djangoproject.com/ticket/28010>.
                # BBB: This extra query can be replaced with
                # select_for_update(of=('self',)) as soon as it's supported in
                # Django.
                Bug.objects.all().select_for_update().get_by_number(self.kwargs['bug_number'])
            return self.queryset.get_by_number(self.kwargs['bug_number'])
        except Bug.DoesNotExist as e:
            raise Http404(*e.args)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bug'] = self.object
        return context


class BugCreateView(BugMutationMixin, FormView):
    template_name = 'buggy/bug_create.html'
    object = None


class AddPresetView(LoginRequiredMixin, View):
    def post(self, request):
        data = request.POST.copy()
        data['user'] = request.user.id
        form = PresetFilterForm(data)
        if form.is_valid():
            form.save()
        else:
            messages.error(request, 'Preset names must be unique.')
        return redirect('buggy:bug_list')


class RemovePresetView(LoginRequiredMixin, View):
    def post(self, request, pk):
        request.user.presetfilter_set.filter(pk=pk).delete()
        return redirect('buggy:bug_list')


class MarkdownPreviewView(LoginRequiredMixin, View):
    def post(self, request):
        return HttpResponse(Comment(comment=request.POST.get('preview', '')).html)
