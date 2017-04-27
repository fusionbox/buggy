import itertools
import os.path
import uuid

from django.db import models, transaction
from django.conf import settings
from django.contrib.postgres.fields import CICharField
from django.utils import timezone
from django import urls
from django.utils.text import get_text_list
from django.utils.translation import ungettext

from enumfields import EnumField, EnumIntegerField

from .enums import State, Priority
from . import verhoeff


class Project(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    name = CICharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def get_absolute_url(self):
        return '{}?projects={}'.format(urls.reverse('buggy:bug_list'), self.id)

    def __str__(self):
        return self.name


class BugQuerySet(models.QuerySet):
    def get_by_number(self, number):
        if verhoeff.validate_verhoeff(number):
            return self.get(pk=number[:-1])
        else:
            raise Bug.DoesNotExist("Bug number checksum doesn't match.")


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
    fulltext = models.TextField()

    objects = BugQuerySet.as_manager()

    def __str__(self):
        return '#{} - {}'.format(self.number, self.title)

    @property
    def number(self):
        return verhoeff.generate_verhoeff(self.id)

    def get_absolute_url(self):
        return urls.reverse('buggy:bug_detail', kwargs={'bug_number': self.number})

    @property
    def actions_preloaded(self):
        return self.actions.select_related(
            'user', 'comment', 'setpriority', 'setassignment__assigned_to',
            'setstate', 'setproject', 'settitle',
        ).prefetch_related('attachments')


class Action(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    bug = models.ForeignKey(Bug, related_name='actions', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        unique_together = [
            ('bug', 'order')
        ]
        ordering = ('bug', 'order')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_operations = []

    @property
    def operations(self):
        return itertools.chain(
            self.pending_operations,
            (
                getattr(self, rel_obj.name)
                for rel_obj in self._meta.get_fields()
                if (
                    rel_obj.one_to_one and
                    rel_obj.target_field.name == 'action' and
                    hasattr(self, rel_obj.name)
                )
            ),
            self.attachments.all(),
        )

    @property
    def description(self):
        descriptions = [i.description for i in self.operations if i.description]

        # we want to group the description of all of the attachments together
        attachment_count = len(self.attachments.all())
        if attachment_count:
            descriptions.append(
                ungettext(
                    'added %(count)s attachment',
                    'added %(count)s attachments',
                    attachment_count
                ) % {'count': attachment_count}
            )

        return '{} {}'.format(
            self.user.get_short_name(),
            get_text_list(descriptions, 'and')
        )

    @classmethod
    @transaction.atomic
    def build_bug(cls, user, title, project, priority, state):
        bug = Bug(
            created_by=user,
        )
        action = cls(
            bug=bug,
            user=user,
            order=0,
        )
        action.set_title(title)
        action.set_project(project)
        action.set_priority(priority)
        action.set_state(state)
        return action

    @classmethod
    def build(cls, user, bug):
        return cls(
            user=user,
            bug=bug,
            # Actions are prefetched by the detail view, so doing this in
            # python instead of the database saves a query.
            order=max(action.order for action in bug.actions.all()) + 1,
        )

    def set_title(self, title):
        operation = SetTitle(title=title)
        self.pending_operations.append(operation)
        return operation

    def set_project(self, project):
        operation = SetProject(project=project)
        self.pending_operations.append(operation)
        return operation

    def set_priority(self, priority):
        operation = SetPriority(priority=priority)
        self.pending_operations.append(operation)
        return operation

    def set_state(self, state):
        operation = SetState(state=state)
        self.pending_operations.append(operation)
        return operation

    def set_assignment(self, assign_to):
        operation = SetAssignment(assigned_to=assign_to)
        self.pending_operations.append(operation)
        return operation

    def add_comment(self, comment):
        operation = Comment(comment=comment)
        self.pending_operations.append(operation)
        return operation

    def add_attachment(self, file):
        operation = AddAttachment(file=file)
        self.pending_operations.append(operation)
        return operation

    @transaction.atomic
    def commit(self):
        pending_operations = self.pending_operations
        # This is reset early because post_save signals on the action could get
        # duplicate operations otherwise.
        self.pending_operations = []

        for operation in pending_operations:
            operation.action = self
            operation.apply()

        self.bug.save()
        self.bug = self.bug
        self.save()

        for operation in pending_operations:
            operation.action = self
            setattr(self, operation._meta.model_name, operation)
            operation.save(force_insert=True)


class Operation(models.Model):
    class Meta:
        abstract = True

    def apply(self):
        pass

    @property
    def description(self):
        return None


class Comment(Operation):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    comment = models.TextField()

    def apply(self):
        self.action.bug.fulltext += ' ' + self.comment

    def compile(self):
        from .markdown import BuggyExtension, safe_markdown
        extension = BuggyExtension()
        html = safe_markdown(self.comment, extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.headerid',
            extension
        ])
        return (html, extension.mentioned_users, extension.mentioned_bugs)

    @property
    def html(self):
        return self.compile()[0]

    @property
    def mentioned_users(self):
        return self.compile()[1]

    @property
    def mentioned_bugs(self):
        return self.compile()[2]


class SetTitle(Operation):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)

    def apply(self):
        self.action.bug.title = self.title
        self.action.bug.fulltext += ' ' + self.title


class SetAssignment(Operation):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    @property
    def description(self):
        return 'assigned the bug to {}'.format(self.assigned_to.get_short_name())

    def apply(self):
        self.action.bug.assigned_to = self.assigned_to


class SetState(Operation):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    state = EnumField(State, max_length=25)

    @property
    def description(self):
        return 'changed the state to {}'.format(self.state.label)

    def apply(self):
        self.action.bug.state = self.state


class SetPriority(Operation):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    priority = EnumIntegerField(Priority)

    @property
    def description(self):
        return 'set the priority to {}'.format(self.priority.label)

    def apply(self):
        self.action.bug.priority = self.priority


class SetProject(Operation):
    action = models.OneToOneField(Action, primary_key=True, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)

    def apply(self):
        self.action.bug.project = self.project


def attachment_upload_to(instance, filename):
    return 'attachments/{}/{}/{}'.format(instance.action.bug.number, uuid.uuid4(), filename)


class AddAttachment(Operation):
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=attachment_upload_to, max_length=255)

    @property
    def basename(self):
        return os.path.basename(self.file.name)

    @property
    def extension(self):
        return os.path.splitext(self.file.name)[1]

    @property
    def is_image(self):
        return self.extension in {'.png', '.jpg', '.gif'}


class PresetFilter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    url = models.CharField(max_length=1000)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [
            ('user', 'name'),
        ]
        ordering = ('name', )
