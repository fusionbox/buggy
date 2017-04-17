from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import Http404
from django.views.generic import ListView, DetailView

from .models import Bug, Action
from .enums import State
from .forms import FilterForm
from . import verhoeff


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
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        if self.form.is_valid():
            return self.form.filter(qs)
        else:
            return qs.none()


class BugDetailView(LoginRequiredMixin, DetailView):
    queryset = Bug.objects.all().prefetch_related(
        Prefetch('actions', queryset=Action.objects.select_related(
            'user', 'comment', 'setpriority', 'setassignment__assigned_to',
            'setstate',
        ))
    ).select_related(
        'created_by', 'assigned_to', 'project'
    )

    def dispatch(self, *args, **kwargs):
        if not verhoeff.validate_verhoeff(self.kwargs['bug_number']):
            raise Http404("Bug number checksum doesn't match")
        else:
            self.kwargs['pk'] = self.kwargs['bug_number'][:-1]
        return super().dispatch(*args, **kwargs)
