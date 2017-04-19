import pytest
from django.contrib.auth import get_user_model

from buggy.models import Bug, Comment
from .fixtures import bug, user, project

User = get_user_model()


def test_get_by_number(bug):
    retrieved_bug = Bug.objects.get_by_number(bug.number)
    assert retrieved_bug == bug


@pytest.mark.django_db
def test_mention_rendering():
    User.objects.create_user(
        email='test@example.com',
        name='Test',
    )

    comment = Comment(comment='@test foo')
    assert comment.html == '<p><span class="mention">@test</span> foo</p>'

    comment = Comment(comment='hello @test foo')
    assert comment.html == '<p>hello <span class="mention">@test</span> foo</p>'

    comment = Comment(comment='hello @test')
    assert comment.html == '<p>hello <span class="mention">@test</span></p>'

    comment = Comment(comment='@notauser foo')
    assert comment.html == '<p>@notauser foo</p>'

    comment = Comment(comment='`@test foo`')
    assert comment.html == '<p><code>@test foo</code></p>'


@pytest.mark.django_db
def test_mentions():
    user = User.objects.create_user(
        email='test@example.com',
        name='Test',
    )

    comment = Comment(comment='test foo')
    assert comment.mentions == set()

    comment = Comment(comment='@test foo')
    assert comment.mentions == {user}

    comment = Comment(comment='`@test foo`')
    assert comment.mentions == set()
