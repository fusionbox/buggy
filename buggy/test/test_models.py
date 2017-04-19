from buggy.models import Bug
from .fixtures import bug, user, project


def test_get_by_number(bug):
    retrieved_bug = Bug.objects.get_by_number(bug.number)
    assert retrieved_bug == bug
