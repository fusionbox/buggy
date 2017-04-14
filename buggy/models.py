from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import CICharField
from django.utils import timezone
from django import urls
from django.utils.text import get_text_list

from enumfields import EnumField, EnumIntegerField
import markdown

from .enums import State, Priority
from . import verhoeff


class Project(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    name = CICharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Bug(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=100)
    state = EnumField(State, max_length=25)
    priority = EnumIntegerField(Priority)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='+'
    )

    def __str__(self):
        return '#{} - {}'.format(self.number, self.title)

    @property
    def number(self):
        return verhoeff.generate_verhoeff(self.id)

    def get_absolute_url(self):
        return urls.reverse('buggy:bug_detail', kwargs={'bug_number': self.number})


class Action(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField()
    bug = models.ForeignKey(Bug, related_name='actions', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        unique_together = [
            ('bug', 'order')
        ]
        ordering = ('bug', 'order')

    @property
    def operations(self):
        return filter(bool, [
            getattr(self, 'setassignment', None),
            getattr(self, 'setstate', None),
            getattr(self, 'setpriority', None),
        ])

    @property
    def description(self):
        return '{} {}'.format(
            self.user.get_short_name(),
            get_text_list([i.description for i in self.operations], 'and')
        )


class Comment(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    comment = models.TextField()

    @property
    def html(self):
        return markdown.markdown(self.comment, extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.headerid',
        ])


class SetTitle(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)


class SetAssignment(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    @property
    def description(self):
        return 'assigned the bug to {}'.format(self.assigned_to.get_short_name())


class SetState(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    state = EnumField(State, max_length=25)

    @property
    def description(self):
        return 'changed the state to {}'.format(self.state)


class SetPriority(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    priority = EnumIntegerField(Priority)

    @property
    def description(self):
        return 'set the priority to {}'.format(self.priority)


class SetProject(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)


class AddAttachment(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/', max_length=255)
