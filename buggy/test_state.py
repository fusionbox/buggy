from collections import defaultdict

import pytest

from django.contrib.auth import get_user_model
from django.utils import timezone

from . import models
from .enums import State, Priority


User = get_user_model()


class ValidationError(Exception):
    pass


class ListRegistry(defaultdict):
    def __init__(self):
        super(ListRegistry, self).__init__(list)

    def register(self, key):
        def inner(fn):
            self[key].append(fn)
            return fn
        return inner


operations_validators = ListRegistry()


def validate_action(bug, action):
    # TODO: catch and aggregate all ValidationErrors
    for key in action.keys():
        for validator in operations_validators[key]:
            validator(bug, action)
    return True


@operations_validators.register(models.Comment)
def comment_may_not_contain_foo(bug, action):
    if 'foo' in action[models.Comment]['comment']:
        raise ValidationError('Comment must not contain foo')


state_validators = ListRegistry()


@operations_validators.register(models.SetState)
def run_state_validations(bug, action):
    next_state = action[models.SetState]['state']
    for state_change_validator in state_validators[next_state]:
        state_change_validator(bug, action)


def can_come_from(predecessors):
    def inner(bug, action):
        if bug.state not in predecessors:
            raise ValidationError('You cannot go to that state.')
    return inner


resolved_states = [
    State.RESOLVED_FIXED,
    State.RESOLVED_UNREPROPDUCIBLE,
    State.RESOLVED_DUPLICATE,
    State.RESOLVED_IMPOSSIBLE,
    State.RESOLVED_NOT_A_BUG,
]


valid_state_go_tos = {
    State.NEW: [State.ENTRUSTED, State.CLOSED],
    State.ENTRUSTED: [*resolved_states, State.CLOSED],
    **{
        state: [State.REOPENED, State.VERIFIED]
        for state in resolved_states
    },
    State.VERIFIED: [State.REOPENED, State.LIVE],
}

for state, targets in valid_state_go_tos.items():
    predecessors = [
        s for s in State
        if state in valid_state_go_tos.get(s, [])
    ]
    state_validators.register(state)(can_come_from(predecessors))


@state_validators.register(State.REOPENED)
def reopening_requires_comment(bug, action):
    if models.Comment not in action:
        raise ValidationError('Reopening bug requires comment')


@state_validators.register(State.RESOLVED_DUPLICATE)
@state_validators.register(State.RESOLVED_NOT_A_BUG)
def cannot_set_title(bug, action):
    if models.SetTitle in action:
        raise ValidationError('Cannot set title')


@pytest.fixture()
def user(db):
    return User.objects.create_user(
        email='test@example.com',
        name='Test User',
        password='password1',
    )


@pytest.fixture()
def project(db):
    return models.Project.objects.create(
        name='Project',
    )


@pytest.mark.django_db
def test_rule1(user, project):
    "Comment must not containt word foo"
    bug = models.Bug.objects.create(
        project=project,
        title='Hello',
        state=State.ENTRUSTED,
        priority=Priority.NORMAL,
        created_by=user,
    )
    good_action = {
        'created_at': timezone.now(),
        'user': user,
        models.Comment: {
            'comment': 'Added a Comment',
        },
    }
    assert validate_action(bug, good_action)

    bad_action = {
        'created_at': timezone.now(),
        'user': user,
        models.Comment: {
            'comment': 'Added a foo',
        },
    }
    with pytest.raises(ValidationError):
        validate_action(bug, bad_action)


@pytest.mark.django_db
def test_rule2(user, project):
    "Cannot set title for some state changes"
    bug = models.Bug.objects.create(
        project=project,
        title='Hello',
        state=State.ENTRUSTED,
        priority=Priority.NORMAL,
        created_by=user,
    )
    assert validate_action(bug, {
        'created_at': timezone.now(),
        'user': user,
        models.SetState: {
            'state': State.RESOLVED_FIXED,
        },
        models.SetTitle: {
            'title': 'New Title',
        }
    })

    for weird_state in [State.RESOLVED_DUPLICATE, State.RESOLVED_NOT_A_BUG]:
        with pytest.raises(ValidationError):
            assert validate_action(bug, {
                'created_at': timezone.now(),
                'user': user,
                models.SetState: {
                    'state': weird_state,
                },
                models.SetTitle: {
                    'title': 'New Title',
                }
            })


@pytest.mark.django_db
def test_reopening_a_bug_requires_comment(user, project):
    bug = models.Bug.objects.create(
        project=project,
        title='Hello',
        state=State.RESOLVED_FIXED,
        priority=Priority.NORMAL,
        created_by=user,
    )
    good_action = {
        'created_at': timezone.now(),
        'user': user,
        models.SetState: {
            'state': State.REOPENED,
        },
        models.Comment: {
            'comment': 'Fails in IE11',
        }
    }
    assert validate_action(bug, good_action)

    bad_action = {
        'created_at': timezone.now(),
        'user': user,
        models.SetState: {
            'state': State.REOPENED,
        },
    }
    with pytest.raises(ValidationError):
        validate_action(bug, bad_action)


@pytest.mark.django_db
def test_can_go_to(user, project):
    bug = models.Bug.objects.create(
        project=project,
        title='Hello',
        state=State.VERIFIED,
        priority=Priority.NORMAL,
        created_by=user,
    )
    assert validate_action(bug, {
        'created_at': timezone.now(),
        'user': user,
        models.SetState: {
            'state': State.REOPENED,
        },
        models.Comment: {
            'comment': 'It does not work if I set my timezone to AEDT',
        }
    })

    with pytest.raises(ValidationError):
        validate_action(bug, {
            'created_at': timezone.now(),
            'user': user,
            models.SetState: {
                'state': State.RESOLVED_FIXED,
            },
        })

    new_bug = models.Bug(
        project=project,
        title='Hello',
        state=State.NEW,
        priority=Priority.NORMAL,
    )
    assert validate_action(new_bug, {
        'created_at': timezone.now(),
        'user': user,
        models.SetState: {
            'state': State.CLOSED,
        }
    })
    assert validate_action(new_bug, {
        'created_at': timezone.now(),
        'user': user,
        models.SetState: {
            'state': State.ENTRUSTED,
        }
    })

    with pytest.raises(ValidationError):
        validate_action(new_bug, {
            'created_at': timezone.now(),
            'user': user,
            models.SetState: {
                'state': State.REOPENED,
            },
        })
