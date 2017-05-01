import re
import hmac
import hashlib

from django.contrib.auth import get_user_model

from .models import Bug
from .mutation import BuggyBugMutator

User = get_user_model()


BUG_RE = re.compile(r'(fix(?:e[ds])?(?:\s+bug(?:gy)?)?)?(?:\s+|^|\W+)#([0-9]+\b)', re.IGNORECASE)


def validate_signature(secret, request_body, signature):
    computed_signature = 'sha1={}'.format(hmac.new(secret, request_body, hashlib.sha1).hexdigest())
    return hmac.compare_digest(signature, computed_signature)


def get_bugs_from_commit_message(msg):
    fixes = set()
    mentions = set()
    for match in BUG_RE.findall(msg):
        if match[0]:
            fixes.add(match[1])
        else:
            mentions.add(match[1])
    return (mentions, fixes)


def process_commit(commit):
    try:
        user = User.objects.get(email=commit['author']['email'])
    except User.DoesNotExist:
        return

    mentions, fixes = get_bugs_from_commit_message(commit['message'])
    for bug_number in mentions | fixes:
        try:
            bug = Bug.objects.get_by_number(bug_number)
        except Bug.DoesNotExist:
            pass
        else:
            past_comments = (
                action.comment.comment for action in bug.actions.all() if hasattr(action, 'comment')
            )
            if not any(commit['id'] in c for c in past_comments):
                mutator = BuggyBugMutator(bug=bug, user=user)
                actions = {a[0] for a in mutator.action_choices(mutator.get_actions())}

                comment = "{} {} the bug in commit `{}`:\n\n{}".format(
                    user.get_short_name(),
                    'fixed' if bug_number in fixes else 'mentioned',
                    commit['id'],
                    commit['message'],
                )
                if bug_number in fixes and 'resolved-fixed' in actions:
                    action = 'resolved-fixed'
                else:
                    action = 'comment'
                mutator.process_action({
                    'comment': comment,
                    'action': action,
                })
