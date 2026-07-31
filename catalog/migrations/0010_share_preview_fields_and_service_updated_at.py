from __future__ import annotations

from django.db import migrations, models
import django.utils.timezone


def populate_share_preview_fields(apps, schema_editor):
    SiteSettings = apps.get_model("catalog", "SiteSettings")

    for site_settings in SiteSettings.objects.all():
        updated_fields = []

        if not site_settings.share_title:
            site_settings.share_title = site_settings.seo_title or "Подари момент | Персональные подарки на заказ"
            updated_fields.append("share_title")

        if not site_settings.share_description:
            site_settings.share_description = (
                site_settings.seo_description
                or "Авторские подарки, фотокниги, наборы и сюрпризы на заказ. "
                "Индивидуальный дизайн, ручная работа и доставка по России."
            )
            updated_fields.append("share_description")

        if not site_settings.share_image_path:
            site_settings.share_image_path = site_settings.hero_image_path or site_settings.logo_path
            updated_fields.append("share_image_path")

        if not site_settings.share_image_alt:
            site_settings.share_image_alt = site_settings.site_name or "Превью ссылки"
            updated_fields.append("share_image_alt")

        if updated_fields:
            site_settings.save(update_fields=updated_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0009_alter_sitesettings_contact_success_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now, verbose_name="Обновлено"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="share_description",
            field=models.TextField(blank=True, verbose_name="Описание превью ссылки"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="share_image_alt",
            field=models.CharField(blank=True, max_length=255, verbose_name="Alt изображения превью ссылки"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="share_image_path",
            field=models.CharField(blank=True, max_length=255, verbose_name="Путь к изображению превью ссылки"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="share_title",
            field=models.CharField(blank=True, max_length=255, verbose_name="Заголовок превью ссылки"),
        ),
        migrations.RunPython(populate_share_preview_fields, migrations.RunPython.noop),
    ]
