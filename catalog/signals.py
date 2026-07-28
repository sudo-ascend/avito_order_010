from __future__ import annotations

from django.apps import apps
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .default_content import ensure_default_content


@receiver(post_migrate)
def bootstrap_catalog_content(sender, **kwargs):
    if sender.name != apps.get_app_config("catalog").name:
        return
    ensure_default_content()
