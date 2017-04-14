import functools
import operator

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q


from .models import Project
from .enums import State, Priority

User = get_user_model()


class FilterForm(forms.Form):
    projects = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Project.objects.filter(is_active=True),
    )
    search = forms.CharField(required=False)
    created_by = forms.ModelChoiceField(
        required=False,
        empty_label='Anyone',
        queryset=User.objects.filter(is_active=True),
    )
    assigned_to = forms.ModelChoiceField(
        empty_label='Anyone',
        required=False,
        queryset=User.objects.filter(is_active=True),
    )

    priority = forms.TypedMultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[(i.value, i.name) for i in Priority],
        coerce=lambda p: Priority(int(p)),
    )

    state = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[
            ('new', 'New'),
            ('entrusted', 'Entrusted'),
            ('resolved', 'Resolved'),
            ('verified', 'Verified'),
            ('reopened', 'Reopened'),
            ('live', 'Live'),
            ('closed', 'Closed'),
        ],
    )

    def __init__(self, data, **kwargs):
        data = data.copy()
        data.setlistdefault('priority', [p.value for p in Priority])
        data.setlistdefault('state', [
            'new', 'entrusted', 'resolved', 'verified', 'reopened', 'live'
        ])
        super().__init__(data=data, **kwargs)

    def filter(self, qs):
        cd = self.cleaned_data
        if cd['projects']:
            qs = qs.filter(project__in=cd['projects'])
        if cd['created_by']:
            qs = qs.filter(created_by=cd['created_by'])
        if cd['assigned_to']:
            qs = qs.filter(created_by=cd['assigned_to'])
        if cd['priority']:
            qs = qs.filter(priority__in=cd['priority'])
        if cd['state']:
            conds = []
            for state in cd['state']:
                conds.extend(
                    Q(state=state_enum)
                    for state_enum in State
                    if state_enum.value == state or state_enum.value.startswith('{}-'.format(state))
                )
            qs = qs.filter(functools.reduce(operator.or_, conds))
        if cd['search']:
            # TODO: actual fulltext search
            qs = qs.filter(
                Q(title__icontains=cd['search']) |
                Q(actions__comment__comment__icontains=cd['search'])
            ).distinct()
        return qs
