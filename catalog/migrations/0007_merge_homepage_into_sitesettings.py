from __future__ import annotations

from django.db import migrations, models
import django.utils.timezone


HOMEPAGE_FIELD_NAMES = (
    "seo_title",
    "seo_description",
    "hero_title",
    "hero_text",
    "hero_primary_text",
    "hero_primary_link",
    "hero_secondary_text",
    "hero_secondary_link",
    "hero_image_path",
    "hero_image_alt",
    "hero_advantages_text",
    "about_title",
    "about_lead",
    "about_text",
    "about_list",
    "about_image_1_path",
    "about_image_1_alt",
    "about_image_2_path",
    "about_image_2_alt",
    "about_image_3_path",
    "about_image_3_alt",
    "catalog_title",
    "works_title",
    "works_button_text",
    "works_button_link",
    "reviews_title",
    "process_title",
    "contact_title",
    "contact_text",
    "contact_image_path",
    "contact_image_alt",
    "contact_success_message",
    "footer_navigation_title",
    "footer_contacts_title",
)


def merge_homepage_into_sitesettings(apps, schema_editor):
    SiteSettings = apps.get_model("catalog", "SiteSettings")
    HomePageSettings = apps.get_model("catalog", "HomePageSettings")

    site_settings = SiteSettings.objects.order_by("pk").first()
    home_settings = HomePageSettings.objects.order_by("pk").first()

    if home_settings is None:
        return

    if site_settings is None:
        site_settings = SiteSettings.objects.create(pk=1)

    updated_fields = []
    for field_name in HOMEPAGE_FIELD_NAMES:
        current_value = getattr(site_settings, field_name, None)
        incoming_value = getattr(home_settings, field_name, None)
        if current_value in ("", None) and incoming_value not in ("", None):
            setattr(site_settings, field_name, incoming_value)
            updated_fields.append(field_name)

    if updated_fields:
        site_settings.save(update_fields=updated_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_sitesettings_max_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="about_image_1_alt",
            field=models.CharField(blank=True, max_length=255, verbose_name="Alt первой картинки блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_image_1_path",
            field=models.CharField(blank=True, max_length=255, verbose_name="Путь к первой картинке блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_image_2_alt",
            field=models.CharField(blank=True, max_length=255, verbose_name="Alt второй картинки блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_image_2_path",
            field=models.CharField(blank=True, max_length=255, verbose_name="Путь ко второй картинке блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_image_3_alt",
            field=models.CharField(blank=True, max_length=255, verbose_name="Alt третьей картинки блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_image_3_path",
            field=models.CharField(blank=True, max_length=255, verbose_name="Путь к третьей картинке блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_lead",
            field=models.TextField(blank=True, verbose_name="Лид блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_list",
            field=models.TextField(blank=True, verbose_name="Список в блоке о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_text",
            field=models.TextField(blank=True, verbose_name="Основной текст блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="about_title",
            field=models.CharField(blank=True, max_length=255, verbose_name="Заголовок блока о нас"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="catalog_title",
            field=models.CharField(default="Наши подарки", max_length=255, verbose_name="Заголовок каталога"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="contact_image_alt",
            field=models.CharField(blank=True, max_length=255, verbose_name="Alt картинки блока контактов"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="contact_image_path",
            field=models.CharField(blank=True, max_length=255, verbose_name="Путь к картинке блока контактов"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="contact_success_message",
            field=models.CharField(default="Спасибо! Мы получили заявку и скоро свяжемся с вами.", max_length=255, verbose_name="Сообщение об успешной отправке"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="contact_text",
            field=models.TextField(blank=True, verbose_name="Текст блока контактов"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="contact_title",
            field=models.CharField(default="Создадим подарок специально для вас", max_length=255, verbose_name="Заголовок контактов"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="footer_contacts_title",
            field=models.CharField(default="Контакты", max_length=120, verbose_name="Заголовок контактов в футере"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="footer_navigation_title",
            field=models.CharField(default="Навигация", max_length=120, verbose_name="Заголовок навигации в футере"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_advantages_text",
            field=models.TextField(blank=True, verbose_name="Преимущества hero"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_image_alt",
            field=models.CharField(blank=True, max_length=255, verbose_name="Alt hero-изображения"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_image_path",
            field=models.CharField(blank=True, max_length=255, verbose_name="Путь к hero-изображению"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_primary_link",
            field=models.CharField(default="#contact", max_length=255, verbose_name="Ссылка основной кнопки hero"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_primary_text",
            field=models.CharField(default="Создать свой подарок", max_length=120, verbose_name="Текст основной кнопки hero"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_secondary_link",
            field=models.CharField(default="#works", max_length=255, verbose_name="Ссылка второй кнопки hero"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_secondary_text",
            field=models.CharField(default="Смотреть работы", max_length=120, verbose_name="Текст второй кнопки hero"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_text",
            field=models.TextField(blank=True, verbose_name="Текст hero"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_title",
            field=models.CharField(default="Подари момент, который останется в памяти", max_length=255, verbose_name="Заголовок hero"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="process_title",
            field=models.CharField(default="Как мы работаем", max_length=255, verbose_name="Заголовок процесса"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="reviews_title",
            field=models.CharField(default="Отзывы", max_length=255, verbose_name="Заголовок отзывов"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="seo_description",
            field=models.TextField(blank=True, verbose_name="SEO description главной"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="seo_title",
            field=models.CharField(blank=True, max_length=255, verbose_name="SEO title главной"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now, verbose_name="Обновлено"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="works_button_link",
            field=models.CharField(blank=True, max_length=255, verbose_name="Ссылка кнопки работ"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="works_button_text",
            field=models.CharField(default="Смотреть больше работ", max_length=120, verbose_name="Текст кнопки работ"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="works_title",
            field=models.CharField(default="Наши работы", max_length=255, verbose_name="Заголовок работ"),
        ),
        migrations.RunPython(merge_homepage_into_sitesettings, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="HomePageSettings",
        ),
    ]
