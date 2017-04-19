import pytest

from django.contrib.auth import get_user_model

from buggy.models import Action, Project
from buggy.enums import Priority, State

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
