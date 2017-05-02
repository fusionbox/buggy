import functools
import operator

from django import forms
from django.contrib.auth import get_user_model

from .models import Project, PresetFilter
from .enums import State, Priority
from .fields import MultipleFileField

User = get_user_model()


class UnwrappedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    option_template_name = 'buggy/forms/widgets/checkbox_option_label_sibling.html'


class FilterForm(forms.Form):
    projects = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Project.objects.filter(is_active=True),
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Enter a search term'}
        ),
    )
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
        widget=UnwrappedCheckboxSelectMultiple,
        choices=[(i.value, i.label) for i in Priority],
        coerce=lambda p: Priority(int(p)),
    )

    state = forms.MultipleChoiceField(
        required=False,
        widget=UnwrappedCheckboxSelectMultiple,
        choices=[
            (State.NEW.value, State.NEW.label),
            (State.ENTRUSTED.value, State.ENTRUSTED.label),
            ('resolved', 'resolved'),
            (State.VERIFIED.value, State.VERIFIED.label),
            (State.REOPENED.value, State.REOPENED.label),
            (State.LIVE.value, State.LIVE.label),
            (State.CLOSED.value, State.CLOSED.label),
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
            qs = qs.filter(assigned_to=cd['assigned_to'])
        if cd['priority']:
            qs = qs.filter(priority__in=cd['priority'])
        if cd['state']:
            qs = qs.filter(state__in={
                state_enum
                for state_enum in State
                for state in cd['state']
                if state_enum.value == state or state_enum.value.startswith('{}-'.format(state))
            })
        if cd['search']:
            # We use extra here instead of the builtin __search filter because
            # it's extremely inefficient when used with .annotate() (we need to
            # annotate in order to set the 'english' config, to match the
            # expression in our functional index).
            # <https://code.djangoproject.com/ticket/28128>
            qs = qs.extra(
                where=[
                    '''
                        to_tsvector('english', COALESCE("buggy_bug"."fulltext", '')) @@
                            plainto_tsquery('english', %s)
                    '''
                ],
                params=[cd['search']]
            )
        return qs


class PresetFilterForm(forms.ModelForm):
    class Meta:
        model = PresetFilter
        fields = ['user', 'name', 'url']
        widgets = {
            'name': forms.TextInput(
                attrs={'placeholder': 'Preset Name'}
            ),
        }


class BugFormBase(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, required=False)
    priority = forms.TypedChoiceField(
        choices=[(i.value, i.label) for i in Priority],
        coerce=lambda p: Priority(int(p)),
        initial=Priority.NORMAL.value,
    )
    assign_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
    )


class EditForm(BugFormBase):
    title = forms.CharField(max_length=100, required=True)
    attachments = MultipleFileField(
        required=False,
    )


class CreateForm(EditForm):
    comment = forms.CharField(widget=forms.Textarea)
    project = forms.ModelChoiceField(queryset=Project.objects.filter(is_active=True))


class BulkActionForm(BugFormBase):
    def __init__(self, *args, **kwargs):
        bug_queryset = kwargs.pop('queryset')
        self.bug_actions = kwargs.pop('bug_actions')
        super().__init__(*args, **kwargs)
        self.fields['bugs'] = forms.ModelMultipleChoiceField(
            queryset=bug_queryset, required=True
        )

    def clean(self):
        super().clean()
        allowed_actions = functools.reduce(
            operator.and_,
            (set(self.bug_actions[bug.number]) for bug in self.cleaned_data['bugs']),
        )
        if self.cleaned_data['action'] not in allowed_actions:
            raise forms.ValidationError("Invalid action for the selected bugs.")
