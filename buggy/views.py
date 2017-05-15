import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, FormView, View
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.db.models import Prefetch
from django.db import transaction
from django.utils.functional import cached_property
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.template.defaultfilters import capfirst, pluralize

from .models import Bug, Action, Comment
from .forms import FilterForm, PresetFilterForm
from .mutation import BuggyBugMutator
from .enums import State, Priority
from . import webhook

User = get_user_model()


class BugListView(LoginRequiredMixin, ListView):
    ORDER_FIELDS = {
        'number': 'id',
        'project': 'project__name',
        'bug': 'title',
        'modified': 'modified_at',
        'creator': 'created_by__name',
        'assigned_to': 'assigned_to__name',
        'state': 'state',
        'priority': 'priority',
    }

    mutator_class = BuggyBugMutator
    queryset = Bug.objects.select_related(
        'project', 'created_by', 'assigned_to'
    ).order_by(
        '-modified_at'
    ).defer('fulltext')  # We don't use the column, so there's no need to detoast a long string.

    context_object_name = 'bugs'
    form_class = FilterForm

    def get_form_kwargs(self):
        return {
            'data': self.request.GET,
            'label_suffix': '',
        }

    def get_form(self):
        return self.form_class(**self.get_form_kwargs())

    def get_bulk_action_form_kwargs(self):
        kwargs = {
            'queryset': self.object_list,
            'bug_actions': self.get_bug_actions(),
        }
        if self.request.POST:
            kwargs['data'] = self.request.POST
        return kwargs

    def get_bulk_action_form(self):
        form_class = self.mutator_class.get_bulk_action_form_class()
        return form_class(**self.get_bulk_action_form_kwargs())

    def get(self, *args, **kwargs):
        self.form = self.get_form()
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = self.get_form()
        self.object_list = self.get_queryset()
        bulk_action_form = self.get_bulk_action_form()
        errors = None
        if bulk_action_form.is_valid():
            try:
                with transaction.atomic():
                    for bug in bulk_action_form.cleaned_data['bugs']:
                        state_machine = self.mutator_class(self.request.user, bug)
                        state_machine.process_action(bulk_action_form.cleaned_data)
            except ValidationError as e:
                errors = e
        else:
            errors = sum(bulk_action_form.errors.values(), [])

        if errors:
            for error in errors:
                messages.error(self.request, 'Bulk Action Failed: {}'.format(error))
        else:
            bug_count = len(bulk_action_form.cleaned_data['bugs'])
            messages.success(
                self.request,
                'Success: {} bug{} updated'.format(bug_count, pluralize(bug_count)),
            )

        return HttpResponseRedirect(self.request.get_full_path())

    def get_bug_actions(self):
        bug_actions = {}
        for bug in self.object_list:
            mutator = self.mutator_class(self.request.user, bug)
            action_choices = mutator.action_choices(mutator.get_actions())
            bug_actions[bug.number] = [x[0] for x in action_choices]
        return bug_actions

    def get_sort_links(self):
        sort_links = {}
        querydict = self.request.GET.copy()
        if '_pjax' in querydict:
            del querydict['_pjax']  # pjax adds this param for cache purposes.

        current_sort, desc = self.sort_type()
        for order_field in self.ORDER_FIELDS.keys():
            if 'desc' in querydict:
                del querydict['desc']
            if current_sort == order_field and not desc:
                querydict['desc'] = True
            querydict['sort'] = order_field
            sort_links[order_field] = '?{}'.format(querydict.urlencode())
        return sort_links

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'bulk_action_form' not in kwargs:
            context['bulk_action_form'] = self.get_bulk_action_form()
        context['form'] = self.form
        context['bulk_actions'] = self.mutator_class.get_bulk_actions()
        context['preset_form'] = PresetFilterForm(label_suffix='')
        context['sort_links'] = self.get_sort_links()
        context['sort_by'], context['sort_desc'] = self.sort_type()
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        if self.form.is_valid():
            qs = self.form.filter(qs)
            order_field, desc = self.sort_type()
            return qs.order_by(('-' if desc else '') + self.ORDER_FIELDS[order_field])
        else:
            return qs.none()

    def get_template_names(self):
        if self.request.META.get('HTTP_X_PJAX'):
            return ['buggy/_bug_list.html']
        else:
            return super().get_template_names()

    def sort_type(self):
        order_field = self.request.GET.get('sort')
        if order_field not in self.ORDER_FIELDS:
            return ('modified', True)
        else:
            return (order_field, bool(self.request.GET.get('desc')))


class BugMutationMixin(LoginRequiredMixin):
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
            } for bug in Bug.objects.exclude(state=State.CLOSED).defer('fulltext')
        ]
        return context

    def form_valid(self, form):
        try:
            action = self.state_machine.process_action(form.cleaned_data)
        except ValidationError as e:
            for error in e.error_list:
                form.add_error(None, e)
            return self.form_invalid(form)
        else:
            messages.success(self.request, capfirst(action.description))
            return HttpResponseRedirect(action.bug.get_absolute_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['label_suffix'] = ''
        return kwargs


class BugDetailView(BugMutationMixin, FormView):
    template_name = 'buggy/bug_detail.html'

    queryset = Bug.objects.select_related(
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

    def get_initial(self):
        return {
            'title': self.object.title,
            'priority': self.object.priority.value,
        }


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


class GitCommitWebhookView(View):
    def post(self, request):
        if settings.GIT_COMMIT_WEBHOOK_SECRET is None or webhook.validate_signature(
            settings.GIT_COMMIT_WEBHOOK_SECRET,
            request.body,
            request.META['HTTP_X_HUB_SIGNATURE'],
        ):
            data = json.loads(request.body.decode('utf-8'))
            for commit in data['commits']:
                webhook.process_commit(commit)
            return HttpResponse('', status=201)
        else:
            return HttpResponseForbidden('Signature does not match.')
