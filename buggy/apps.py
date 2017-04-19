from django.db import transaction
from django.db.models.signals import post_save
from django.apps import AppConfig

from .notifications import send_notifications


class BuggyConfig(AppConfig):
    name = 'buggy'

    def ready(self):
        from .models import Action
        post_save.connect(self.on_action_save, sender=Action)

    def on_action_save(self, sender, instance, created, raw, **kwargs):
        if created and not raw:
            transaction.on_commit(lambda: send_notifications(instance))
