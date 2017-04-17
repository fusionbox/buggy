import pytest

from django.contrib.auth import get_user_model

from .models import Action, Project, Bug
from .enums import Priority, State

User = get_user_model()


@pytest.fixture()
def user(db):
    return User.objects.create_user(
        email='test@example.com',
        name='Test User',
        password='password1',
    )


@pytest.fixture()
def project(db):
    return Project.objects.create(
        name='Project',
    )


@pytest.fixture()
def bug(user, project):
    action = Action.build_bug(
        user=user,
        title='title',
        project=project,
        priority=Priority.URGENT,
        state=State.NEW,
    )
    action.commit()
    return action.bug


def test_create_bug(user, project):
    action = Action.build_bug(
        user=user,
        title='title',
        project=project,
        priority=Priority.URGENT,
        state=State.NEW,
    )
    assert Bug.objects.count() == 0, "the bug should not be created yet"
    action.commit()

    bug = Bug.objects.get()
    assert bug.title == 'title'
    assert bug.project == project
    assert bug.priority == Priority.URGENT
    assert bug.state == State.NEW
    assert bug.created_by == user


def test_edit_bug(user, bug):
    action = Action.build(bug=bug, user=user)
    action.set_title('new title')

    assert bug.actions.count() == 1, "Action should not be created yet"

    action.commit()

    assert bug.actions.count() == 2
    bug.refresh_from_db()
    assert bug.title == 'new title'


def test_operations(user, bug):
    action = Action.build(bug=bug, user=user)
    assert list(action.operations) == []

    op1 = action.add_comment('bar')
    assert list(action.operations) == [op1]

    op2 = action.set_title('foo')
    assert list(action.operations) == [op1, op2]

    action.commit()
    assert list(action.operations) == [op1, op2]

    action.refresh_from_db()
    assert list(action.operations) == [op1, op2]
