from django.contrib.auth import get_user_model

from markdown.inlinepatterns import Pattern
from markdown.extensions import Extension
from markdown.util import etree
import markdown
import bleach

from buggy.models import Bug

User = get_user_model()


class MentionPattern(Pattern):
    def __init__(self, *args, **kwargs):
        self.extension = kwargs.pop('extension')
        super().__init__(*args, **kwargs)

    def handleMatch(self, match):
        try:
            user = User.objects.filter(name__iexact=match.group(3)).get()
        except User.DoesNotExist:
            return None
        else:
            self.extension.mentioned_users.add(user)
            el = etree.Element('span', {'class': 'mention'})
            el.text = '@{}'.format(match.group(3))
            return el


class BugNumberPattern(Pattern):
    def __init__(self, *args, **kwargs):
        self.extension = kwargs.pop('extension')
        super().__init__(*args, **kwargs)

    def handleMatch(self, match):
        try:
            bug = Bug.objects.get_by_number(match.group(3))
        except Bug.DoesNotExist:
            return None
        else:
            self.extension.mentioned_bugs.add(bug)
            el = etree.Element('a', {
                'href': bug.get_absolute_url(),
                'title': '{} - {}'.format(bug.project, bug.title),
                'class': 'bugLink',
            })
            el.text = '#{}'.format(match.group(3))
            return el


class BuggyExtension(Extension):
    def __init__(self, *args, **kwargs):
        self.mentioned_users = set()
        self.mentioned_bugs = set()
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns['mention'] = MentionPattern(r'(^|(?<=\s))@([A-z]+)\b', extension=self)
        md.inlinePatterns['bugnumber'] = BugNumberPattern(r'(^|(?<=\s))#(\d+)\b', extension=self)


def safe_markdown(comment, extensions=[]):
    html = markdown.markdown(comment, extensions=extensions)
    return bleach.clean(
        text=html,
        tags=[
            'a', 'abbr', 'acronym', 'b', 'blockqote', 'code', 'em', 'i', 'li',
            'ol', 'strong', 'ul', 'p', 'span', 'h1', 'h2', 'h3', 'pre',
            'blockquote', 'table', 'thead', 'tr', 'th', 'td', 'tbody', 'dl',
            'dt', 'sup', 'div', 'hr',
        ],
        attributes={
            '*': ['class'],
            'a': ['href', 'title', 'class', 'id'],
            'acronym': ['title'],
            'abbr': ['title'],
            'sup': ['id'],
            'li': ['id']
        },
    )
