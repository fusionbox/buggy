import json

from django.urls import reverse

from buggy.webhook import get_bugs_from_commit_message, process_commit, validate_signature
from buggy.enums import State

from .fixtures import bug, project, user


def test_get_bugs_from_commit_message():
    assert get_bugs_from_commit_message('#1234') == ({'1234'}, set())
    assert get_bugs_from_commit_message('foo bar #1234 and #456') == ({'1234', '456'}, set())
    assert get_bugs_from_commit_message('fo#1234') == (set(), set())
    assert get_bugs_from_commit_message('(#123)') == ({'123'}, set())

    assert get_bugs_from_commit_message('fixes #123') == (set(), {'123'})
    assert get_bugs_from_commit_message('fixes #123 and fixes #456') == (set(), {'123', '456'})
    assert get_bugs_from_commit_message('fixes #123 and mentions #456') == ({'456'}, {'123'})
    assert get_bugs_from_commit_message('fixed #123') == (set(), {'123'})
    assert get_bugs_from_commit_message('fix #123') == (set(), {'123'})
    assert get_bugs_from_commit_message('fix bug #123') == (set(), {'123'})
    assert get_bugs_from_commit_message('fix buggy #123') == (set(), {'123'})


def test_mention(bug):
    message = "this is related to #{}".format(bug.number)

    commit = {
        "author": {
            "email": bug.created_by.email,
        },
        "id": "dfe96070ea1f472fb3aa35f8a64ede598cb970e0",
        "message": message,
    }
    process_commit(commit)
    assert len(bug.actions.all()) == 2
    action = bug.actions.last()
    assert message in action.comment.comment

    # don't do duplicate comments (pushes from other branches)
    process_commit(commit)
    assert len(bug.actions.all()) == 2


def test_resolve(bug):
    message = "fixes #{}".format(bug.number)

    commit = {
        "author": {
            "email": bug.created_by.email,
        },
        "id": "dfe96070ea1f472fb3aa35f8a64ede598cb970e0",
        "message": message,
    }
    process_commit(commit)
    assert len(bug.actions.all()) == 2
    action = bug.actions.last()
    assert message in action.comment.comment
    assert action.setstate.state == State.RESOLVED_FIXED

    # don't do duplicate comments (pushes from other branches)
    process_commit(commit)
    assert len(bug.actions.all()) == 2

    commit = {
        "author": {
            "email": bug.created_by.email,
        },
        "id": "adc83b19e793491b1c6ea0fd8b46cd9f32e592fc",
        "message": message,
    }

    # needs to validate that the state transition is valid
    process_commit(commit)
    action = bug.actions.last()
    assert not hasattr(action, 'setstate')


def test_view(client, bug, settings):
    settings.GIT_COMMIT_WEBHOOK_SECRET = None

    message = "fixes #{}".format(bug.number)
    response = client.post(reverse('buggy:git_commit_webhook'), json.dumps({
        "commits": [
            {
                "author": {
                    "email": bug.created_by.email,
                },
                "id": "fe0aeff2fe77208d0c5ed4e7b3c1f89ce41a5d35",
                "message": message,
            }
        ],
    }), content_type='application/json')

    assert response.status_code == 201
    action = bug.actions.last()
    assert message in action.comment.comment
    assert action.setstate.state == State.RESOLVED_FIXED


def test_signature():
    assert validate_signature(b'secret', b'body', 'sha1=a18991ff7e4513a1c2d2ee51e3a8e99ca891d9cd')
    assert not validate_signature(b'secret', b'no', 'sha1=a18991ff7e4513a1c2d2ee51e3a8e99ca891d9cd')
