from __future__ import annotations

from unittest.mock import Mock, patch

from django.contrib import admin
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .models import Application, Service, SiteSettings, Step, TelegramSubscriber, WorkExample
from .seo import DEFAULT_HOME_DESCRIPTION, DEFAULT_HOME_TITLE
from .utils import notify_application


class CatalogBaseTestCase(TestCase):
    def setUp(self):
        self.site_settings = SiteSettings.objects.create(
            site_name="Подари момент",
            email="hello@example.com",
            application_email="notify@example.com",
            contact_success_message="Создаем моменты счастья",
        )
        self.service = Service.objects.create(
            title="Тестовый подарок",
            description="Описание",
            is_active=True,
        )


class ApplicationApiTests(CatalogBaseTestCase):
    @patch("catalog.api.notify_application")
    def test_application_api_creates_record(self, notify_application_mock):
        response = self.client.post(
            reverse("catalog:application_create_api"),
            data={
                "name": "Иван",
                "phone": "+7 (921) 111-22-33",
                "email": "ivan@example.com",
                "service": self.service.pk,
                "comment": "Нужен подарок к пятнице",
                "consent": "on",
                "website": "",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Application.objects.count(), 1)

        application = Application.objects.get()
        self.assertEqual(application.service, self.service)
        self.assertEqual(application.source, "website")
        self.assertEqual(application.user_agent, "")
        self.assertTrue(response.json()["ok"])
        notify_application_mock.assert_called_once()

    def test_application_api_returns_field_errors(self):
        response = self.client.post(
            reverse("catalog:application_create_api"),
            data={
                "name": "A",
                "phone": "123",
                "service": "",
                "comment": "https://spam.example",
                "website": "",
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertIn("name", payload["errors"])
        self.assertIn("phone", payload["errors"])
        self.assertIn("service", payload["errors"])
        self.assertIn("comment", payload["errors"])
        self.assertIn("consent", payload["errors"])


class HomePageImageTests(CatalogBaseTestCase):
    def test_hero_advantages_use_distinct_default_icons(self):
        home_settings = SiteSettings.objects.first()
        home_settings.hero_advantages_text = "\n".join(
            [
                "Первое преимущество",
                "Второе преимущество",
                "Третье преимущество",
                "Четвертое преимущество",
                "Пятое преимущество",
                "Шестое преимущество",
            ]
        )
        home_settings.save(update_fields=["hero_advantages_text"])

        self.assertEqual(
            [item["icon"] for item in home_settings.hero_advantages],
            ["heart", "brush", "spark", "truck", "home", "check"],
        )

    def test_home_page_uses_images_from_settings(self):
        SiteSettings.objects.update(
            about_image_1_path="catalog/assets/images/custom/about-1.webp",
            about_image_1_alt="Первая карточка",
            about_image_2_path="catalog/assets/images/custom/about-2.webp",
            about_image_2_alt="Вторая карточка",
            about_image_3_path="catalog/assets/images/custom/about-3.webp",
            about_image_3_alt="Третья карточка",
            contact_image_path="catalog/assets/images/custom/contact.webp",
            contact_image_alt="Подарочная коробка",
        )

        response = self.client.get(reverse("catalog:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["about_images"],
            [
                {"src": "catalog/assets/images/custom/about-1.webp", "alt": "Первая карточка"},
                {"src": "catalog/assets/images/custom/about-2.webp", "alt": "Вторая карточка"},
                {"src": "catalog/assets/images/custom/about-3.webp", "alt": "Третья карточка"},
            ],
        )
        self.assertContains(response, "catalog/assets/images/custom/contact.webp")

    def test_home_page_renders_max_links_when_configured(self):
        max_url = "https://max.ru/podary-moment"
        SiteSettings.objects.update(max_url=max_url)

        response = self.client.get(reverse("catalog:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, max_url, count=3)
        self.assertContains(response, "MAX")

    def test_home_page_renders_links_to_product_detail_pages(self):
        WorkExample.objects.create(
            title="Work example",
            image_path="catalog/assets/images/custom/about-1.webp",
            show_on_home=True,
        )

        response = self.client.get(reverse("catalog:index"))
        detail_url = reverse("catalog:product_detail", args=[self.service.pk])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, detail_url, count=3)


class ProductDetailPageTests(CatalogBaseTestCase):
    def test_product_detail_page_renders_gallery_and_prefilled_form(self):
        self.service.extra_image_paths = [
            "catalog/assets/images/custom/about-1.webp",
            "catalog/assets/images/custom/about-2.webp",
        ]
        self.service.save(update_fields=["extra_image_paths"])

        response = self.client.get(reverse("catalog:product_detail", args=[self.service.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["application_form"].initial["service"], self.service.pk)
        self.assertContains(response, 'data-product-detail-gallery')
        self.assertContains(response, self.service.title)

    def test_product_detail_page_outputs_product_seo_meta(self):
        self.service.description = "Авторский подарок для особого случая с индивидуальным оформлением."
        self.service.category = "Подарки"
        self.service.save(update_fields=["description", "category"])

        response = self.client.get(reverse("catalog:product_detail", args=[self.service.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"<link rel=\"canonical\" href=\"http://testserver/products/{self.service.pk}/\">", html=True)
        self.assertContains(response, '<meta property="og:type" content="product">', html=True)
        self.assertContains(response, self.service.title)
        self.assertContains(response, "BreadcrumbList")
        self.assertContains(response, '"@type":"Product"')


class SeoSurfaceTests(CatalogBaseTestCase):
    def test_home_page_outputs_hardcoded_seo_and_share_preview_tags(self):
        SiteSettings.objects.update(
            share_title="Подарки, которые хочется переслать друзьям",
            share_description="Красивое превью ссылки для мессенджеров и соцсетей.",
            share_image_path="catalog/assets/images/custom/about-1.webp",
            share_image_alt="Превью ссылки",
        )

        response = self.client.get(reverse("catalog:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"<title>{DEFAULT_HOME_TITLE}</title>", html=True)
        self.assertContains(response, f'<meta name="description" content="{DEFAULT_HOME_DESCRIPTION}">', html=True)
        self.assertContains(response, '<meta property="og:type" content="website">', html=True)
        self.assertContains(response, 'content="Подарки, которые хочется переслать друзьям"')
        self.assertContains(response, 'content="Красивое превью ссылки для мессенджеров и соцсетей."')
        self.assertContains(response, '<link rel="canonical" href="http://testserver/">', html=True)
        self.assertContains(response, '"@type":"CollectionPage"')
        self.assertContains(response, '"@type":"ItemList"')

    def test_robots_and_sitemap_expose_public_pages(self):
        robots_response = self.client.get(reverse("catalog:robots_txt"))
        sitemap_response = self.client.get("/sitemap.xml")

        self.assertEqual(robots_response.status_code, 200)
        self.assertContains(robots_response, "Disallow: /admin/")
        self.assertContains(robots_response, "Disallow: /api/")
        self.assertContains(robots_response, "Sitemap: http://testserver/sitemap.xml")
        self.assertEqual(sitemap_response.status_code, 200)
        self.assertContains(sitemap_response, reverse("catalog:index"))
        self.assertContains(sitemap_response, reverse("catalog:product_detail", args=[self.service.pk]))


class AdminImageFieldTests(TestCase):
    def test_image_path_fields_are_hidden_in_admin_forms(self):
        request = RequestFactory().get("/admin/")

        cases = [
            (
                SiteSettings,
                {
                    "logo_upload",
                    "favicon_upload",
                    "share_image_upload",
                    "hero_image_upload",
                    "about_image_1_upload",
                    "about_image_2_upload",
                    "about_image_3_upload",
                    "contact_image_upload",
                },
                {
                    "logo_path",
                    "favicon_path",
                    "share_image_path",
                    "hero_image_path",
                    "about_image_1_path",
                    "about_image_2_path",
                    "about_image_3_path",
                    "contact_image_path",
                },
            ),
            (Service, {"image_upload", "extra_image_uploads"}, {"image_path", "extra_image_paths"}),
            (WorkExample, {"image_upload"}, {"image_path"}),
            (Step, {"icon_upload"}, {"icon_path"}),
        ]

        for model, expected_uploads, hidden_fields in cases:
            form_class = admin.site._registry[model].get_form(request)
            self.assertTrue(expected_uploads.issubset(form_class.base_fields.keys()))
            self.assertTrue(hidden_fields.isdisjoint(form_class.base_fields.keys()))

        site_settings_form = admin.site._registry[SiteSettings].get_form(request)
        self.assertIn("telegram_url", site_settings_form.base_fields)
        self.assertIn("whatsapp_url", site_settings_form.base_fields)
        self.assertIn("max_url", site_settings_form.base_fields)
        self.assertIn("share_title", site_settings_form.base_fields)
        self.assertIn("share_description", site_settings_form.base_fields)
        self.assertNotIn("telegram_username", site_settings_form.base_fields)
        self.assertNotIn("whatsapp_phone", site_settings_form.base_fields)
        self.assertNotIn("seo_title", site_settings_form.base_fields)
        self.assertNotIn("seo_description", site_settings_form.base_fields)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    APPLICATION_NOTIFICATION_EMAIL="notify@example.com",
    TELEGRAM_BOT_TOKEN="",
    TELEGRAM_CHAT_ID="",
)
class NotificationTests(CatalogBaseTestCase):
    def test_notify_application_sends_html_email(self):
        application = Application.objects.create(
            name="Иван",
            phone="+7 (921) 111-22-33",
            email="ivan@example.com",
            service=self.service,
            comment="Позвоните сегодня",
        )

        result = notify_application(application, self.site_settings)

        self.assertTrue(result["email"])
        self.assertFalse(result["telegram"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Новая заявка с сайта")
        self.assertEqual(len(mail.outbox[0].alternatives), 1)

    @override_settings(TELEGRAM_BOT_TOKEN="test-bot-token")
    @patch("catalog.utils.requests.post")
    def test_notify_application_sends_to_all_active_subscribers(self, requests_post_mock):
        requests_post_mock.return_value = Mock()
        requests_post_mock.return_value.raise_for_status.return_value = None
        TelegramSubscriber.objects.create(chat_id="111", username="first", is_active=True)
        TelegramSubscriber.objects.create(chat_id="222", username="second", is_active=True)
        TelegramSubscriber.objects.create(chat_id="333", username="inactive", is_active=False)
        application = Application.objects.create(
            name="Иван",
            phone="+7 (921) 111-22-33",
            service=self.service,
        )

        result = notify_application(application, self.site_settings)

        self.assertTrue(result["telegram"])
        self.assertEqual(requests_post_mock.call_count, 2)
        chat_ids = sorted(call.kwargs["data"]["chat_id"] for call in requests_post_mock.call_args_list)
        self.assertEqual(chat_ids, ["111", "222"])


class TelegramBotCommandTests(TestCase):
    @override_settings(TELEGRAM_BOT_TOKEN="")
    def test_run_telegram_bot_requires_token(self):
        with self.assertRaisesMessage(CommandError, "TELEGRAM_BOT_TOKEN is not configured."):
            call_command("run_telegram_bot")

    @override_settings(TELEGRAM_BOT_TOKEN="test-bot-token")
    @patch("catalog.management.commands.run_telegram_bot.asyncio.run")
    @patch("catalog.management.commands.run_telegram_bot.run_bot", new_callable=Mock)
    def test_run_telegram_bot_starts_aiogram_runner(self, run_bot_mock, asyncio_run_mock):
        run_bot_mock.return_value = object()

        call_command("run_telegram_bot", "--drop-pending-updates")

        run_bot_mock.assert_called_once_with(drop_pending_updates=True)
        asyncio_run_mock.assert_called_once_with(run_bot_mock.return_value)
