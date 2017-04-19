import ogmios


def send_notifications(action):
    # Prevents notification users of their on actions and notifying about the
    # same action twice.
    blacklist = {action.user}

    if hasattr(action, 'setassignment') and action.setassignment.assigned_to not in blacklist:
        blacklist.add(action.setassignment.assigned_to)
        ogmios.send_email('buggy/mail/bug_assigned.md', {
            'bug': action.bug,
            'action': action,
            'assigned_to': action.setassignment.assigned_to,
        })

    if hasattr(action, 'comment'):
        for mention in action.comment.mentioned_users - blacklist:
            ogmios.send_email('buggy/mail/bug_mention.md', {
                'bug': action.bug,
                'action': action,
                'to': mention,
            })
