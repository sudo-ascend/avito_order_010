from __future__ import annotations

import re

from django.db import migrations, models


def _normalize_telegram_url(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.startswith(("http://", "https://")):
        return raw
    if raw.startswith(("t.me/", "telegram.me/")):
        return f"https://{raw}"
    return f"https://t.me/{raw.lstrip('@/')}"


def _normalize_whatsapp_url(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.startswith(("http://", "https://")):
        return raw
    if raw.startswith(("wa.me/", "api.whatsapp.com/", "whatsapp.com/", "www.whatsapp.com/")):
        return f"https://{raw}"

    digits = re.sub(r"\D+", "", raw)
    if digits.startswith("8"):
        digits = f"7{digits[1:]}"
    elif len(digits) == 10:
        digits = f"7{digits}"

    if digits:
        return f"https://wa.me/{digits}"
    return raw


def migrate_social_links_forward(apps, schema_editor):
    SiteSettings = apps.get_model("catalog", "SiteSettings")

    for site_settings in SiteSettings.objects.all():
        telegram_url = _normalize_telegram_url(getattr(site_settings, "telegram_url", ""))
        whatsapp_url = _normalize_whatsapp_url(getattr(site_settings, "whatsapp_url", ""))

        updated_fields = []
        if telegram_url != getattr(site_settings, "telegram_url", ""):
            site_settings.telegram_url = telegram_url
            updated_fields.append("telegram_url")
        if whatsapp_url != getattr(site_settings, "whatsapp_url", ""):
            site_settings.whatsapp_url = whatsapp_url
            updated_fields.append("whatsapp_url")

        if updated_fields:
            site_settings.save(update_fields=updated_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0010_share_preview_fields_and_service_updated_at"),
    ]

    operations = [
        migrations.RenameField(
            model_name="sitesettings",
            old_name="telegram_username",
            new_name="telegram_url",
        ),
        migrations.RenameField(
            model_name="sitesettings",
            old_name="whatsapp_phone",
            new_name="whatsapp_url",
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="telegram_url",
            field=models.URLField(blank=True, verbose_name="Telegram URL"),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="whatsapp_url",
            field=models.URLField(blank=True, verbose_name="WhatsApp URL"),
        ),
        migrations.RunPython(migrate_social_links_forward, migrations.RunPython.noop),
    ]
