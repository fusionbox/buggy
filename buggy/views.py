from django.views.generic import ListView, DetailView
from django.http import Http404
from django.db.models import Prefetch

from .models import Bug, Action
from .enums import State
from . import verhoeff


class BugListView(ListView):
    queryset = Bug.objects.select_related(
        'project', 'created_by', 'assigned_to'
    ).order_by(
        '-modified_at'
    ).exclude(
        state=State.CLOSED
    )
    context_object_name = 'bugs'


class BugDetailView(DetailView):
    queryset = Bug.objects.all().prefetch_related(
        Prefetch('actions', queryset=Action.objects.select_related(
            'user', 'comment'
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
