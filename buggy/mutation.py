from django.core.exceptions import ValidationError
from django import forms
from django.utils.functional import cached_property

from .forms import CreateForm, EditForm
from .models import Action
from .enums import State


class BugMutator(object):
    def __init__(self, user, bug):
        self.bug = bug
        self.user = user

    def get_actions(self):
        raise NotImplementedError

    def process_form(self, form):
        raise NotImplementedError

    def action_choices(self, actions=None):
        for action in (actions or self.get_actions()):
            if 'sub_actions' in action:
                yield from self.action_choices(action['sub_actions'])
            else:
                yield (action['action'], action['label'])


class BuggyBugMutator(BugMutator):
    def get_form_class(self):
        if self.bug:
            base = EditForm
        else:
            base = CreateForm

        class Form(base):
            action = forms.ChoiceField(
                choices=self.action_choices(),
            )

        return Form

    RESOLVED_STATES = {
        State.RESOLVED_FIXED,
        State.RESOLVED_UNREPRODUCIBLE,
        State.RESOLVED_DUPLICATE,
        State.RESOLVED_IMPOSSIBLE,
        State.RESOLVED_NOT_A_BUG,
    }

    def get_actions(self):
        if self.bug:
            state = self.bug.state
        else:
            state = None

        if state == State.NEW:
            return [self.resolved, self.entrusted, self.comment]
        elif state == State.ENTRUSTED:
            return [self.resolved, self.comment]
        elif state in self.RESOLVED_STATES:
            return [self.verified, self.reopened, self.live, self.closed, self.comment]
        elif state == State.REOPENED:
            return [self.resolved, self.entrusted, self.comment]
        elif state == State.LIVE:
            return [self.reopened, self.closed, self.comment]
        elif state == State.CLOSED:
            return [self.reopened, self.comment]
        elif state == State.VERIFIED:
            return [self.reopened, self.live, self.closed, self.comment]
        elif state is None:
            return [
                {'action': 'create', 'label': 'Create', 'help_text': "Create a bug."},
            ]
        else:
            assert False, 'Unknown state %s' % state

    @property
    def comment(self):
        return {
            'action': 'comment',
            'label': 'Comment',
            'help_text': "Leave a comment on the bug or change its priority or assignee",
        }

    @property
    def verified(self):
        return {
            'action': State.VERIFIED.value,
            'label': 'Verify',
            'help_text': (
                "You have verified that this bug is fixed."
            ) + self.resolver_assign_text,
        }

    @property
    def live(self):
        return {
            'action': State.LIVE.value,
            'label': 'Pushed live',
            'help_text': "You have made the change on the live site.",
        }

    @property
    def reopened(self):
        return {
            'action': State.REOPENED.value,
            'label': "Reopen",
            'help_text': (
                "The bug is not resolved. A comment is required to reopen."
            ) + self.resolver_assign_text,
        }

    @property
    def closed(self):
        return {
            'action': State.CLOSED.value,
            'label': "Close",
            'help_text': (
                "This bug has been resolved and verified, it is no longer an issue. "
                "The bug will no longer be in the default view on the homepage.",
            )
        }

    @property
    def entrusted(self):
        return {
            'action': State.ENTRUSTED.value,
            'label': "Entrust",
            'help_text': "You would like to make someone responsible for the bug.",
        }

    @property
    def resolved(self):
        return {
            'action': 'resolve',
            'label': "Resolve",
            'help_text': (
                "You have fixed the bug, or there is a problem "
                "with the bug that its creator must rectify."
            ) + self.creator_assign_text,
            'sub_actions': [
                {
                    'action': State.RESOLVED_FIXED.value,
                    'label': State.RESOLVED_FIXED.label,
                    'help_text': "You have fixed the bug",
                },
                {
                    'action': State.RESOLVED_DUPLICATE.value,
                    'label': State.RESOLVED_DUPLICATE.label,
                    'help_text': (
                        "The bug is a duplicate of another. "
                        "Consider leaving a comment with #bugnumber."
                    ),
                },
                {
                    'action': State.RESOLVED_IMPOSSIBLE.value,
                    'label': State.RESOLVED_IMPOSSIBLE.label,
                    'help_text': "It is not possible to fix the bug.",
                },
                {
                    'action': State.RESOLVED_UNREPRODUCIBLE.value,
                    'label': State.RESOLVED_UNREPRODUCIBLE.label,
                    'help_text': (
                        "You could not reproduce the bug, "
                        "or require more information to do so."
                    ),
                },
                {
                    'action': State.RESOLVED_NOT_A_BUG.value,
                    'label': State.RESOLVED_NOT_A_BUG.label,
                    'help_text': "The bug is by design or intentional.",
                },

            ],
        }

    @property
    def resolver_assign_text(self):
        if self.bug and self.latest_resolver:
            return " Unless you pick another assignee, the bug will be assigned to {}.".format(
                self.latest_resolver.get_short_name()
            )
        else:
            return ''

    @property
    def creator_assign_text(self):
        if self.bug and self.bug.created_by:
            return " Unless you pick another assignee, the bug will be assigned to {}.".format(
                self.bug.created_by.get_short_name()
            )
        else:
            return ''

    def process_form(self, form):
        errors = []
        data = form.cleaned_data

        if data['action'] == State.ENTRUSTED.value \
                and not (self.bug.assigned_to or data['assign_to']):
            errors.append('You must assign the bug to entrust it.')

        if data['action'] == State.REOPENED.value and not data['comment']:
            errors.append('You must leave a comment to reopen the bug.')

        if errors:
            raise ValidationError(errors)

        action = self.perform_mutations(data)
        if not any(action.operations):
            raise ValidationError('Do something at least')
        else:
            action.commit()
        return action

    def perform_mutations(self, data):
        if self.bug:
            action = Action.build(
                bug=self.bug,
                user=self.user
            )
        else:
            action = Action.build_bug(
                user=self.user,
                title=data['title'],
                project=data['project'],
                priority=data['priority'],
                state=State.ENTRUSTED if data['assign_to'] else State.NEW,
            )

        if data['comment']:
            action.add_comment(data['comment'])

        assign_to = None
        if data['assign_to']:
            assign_to = data['assign_to']
        elif data['action'] in {i.value for i in self.RESOLVED_STATES}:
            assign_to = self.bug.created_by
        elif data['action'] in {State.REOPENED.value, State.VERIFIED.value}:
            assign_to = self.latest_resolver

        if assign_to and assign_to != action.bug.assigned_to:
            action.set_assignment(assign_to)

        if data['action'] in {i.value for i in State}:
            action.set_state(State(data['action']))

        if data['priority'] != self.bug.priority:
            action.set_priority(data['priority'])

        for attachment in data['attachments']:
            action.add_attachment(attachment)

        return action

    @cached_property
    def latest_resolver(self):
        for action in reversed(self.bug.actions.all()):
            if hasattr(action, 'setstate') and action.setstate.state in self.RESOLVED_STATES:
                return action.user
