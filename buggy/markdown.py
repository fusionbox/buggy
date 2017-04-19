from django.contrib.auth import get_user_model

from markdown.inlinepatterns import Pattern
from markdown.extensions import Extension
from markdown.util import etree

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
            self.extension.mentions.add(user)
            el = etree.Element('span', {'class': 'mention'})
            el.text = '@{}'.format(match.group(3))
            return el


class MentionExtension(Extension):
    def __init__(self, *args, **kwargs):
        self.mentions = set()
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns['mention'] = MentionPattern(r'(^|(?<=\s))@([A-z]+)\b', extension=self)
