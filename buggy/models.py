from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import CICharField
from django.utils import timezone

from enumfields import EnumField, EnumIntegerField

from .enums import State, Priority


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


class Comment(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    comment = models.TextField()


class SetTitle(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)


class SetAssignment(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class SetState(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    state = EnumField(State, max_length=25)


class SetPriority(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    priority = EnumIntegerField(Priority)


class SetProject(models.Model):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)


class AddAttachment(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/', max_length=255)
