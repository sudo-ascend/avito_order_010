from __future__ import annotations

import json

from django.conf import settings
from django.db import transaction

from .models import Review, Service, SiteSettings, Step, WorkExample

PRODUCT_DATA_FILES = (
    settings.BASE_DIR / "catalog" / "data" / "products.json",
    settings.BASE_DIR / "wb_seller_250129339_full" / "products.json",
)
PRODUCT_IMAGES_DIR = settings.BASE_DIR / "catalog" / "static" / "catalog" / "assets" / "images" / "products"

DEFAULT_HERO_ADVANTAGES = [
    "Индивидуальный подход",
    "Ручная работа с вниманием к деталям",
    "Быстрое изготовление",
    "Доставка по миру",
    "Доставка по РФ",
]

DEFAULT_STEPS = [
    ("1. Вы рассказываете идею", "Пишите нам о том, какой подарок вы хотите подарить.", "catalog/assets/images/custom/step-idea.webp"),
    ("2. Мы создаем дизайн", "Разрабатываем уникальный макет и согласовываем его с вами.", "catalog/assets/images/custom/step-design.webp"),
    ("3. Изготавливаем подарок", "Создаем ваш заказ с любовью и вниманием к деталям.", "catalog/assets/images/custom/step-gift.webp"),
    ("4. Вы получаете момент счастья", "Получаете готовый подарок, который дарит эмоции.", "catalog/assets/images/custom/step-happiness.webp"),
]

DEFAULT_REVIEWS = [
    (5, "Все очень понравилось. Заказ пришел аккуратный, красиво оформленный и качественный."),
    (5, "Очень довольна результатом. Все сделано аккуратно и с вниманием к деталям."),
    (4, "Хорошая работа, красиво и достойно выглядит. В целом осталась довольна."),
    (5, "Спасибо за прекрасную работу. Получилось красиво, аккуратно и с душой."),
]

DEFAULT_SITE_POLICY_TEXT = """
Мы бережно относимся к персональным данным и используем их только для обработки заявок, обратной связи и согласования заказа.

Оставляя заявку на сайте, пользователь подтверждает согласие на обработку имени, телефона, email и комментария, если он указан в форме.

Данные не передаются третьим лицам, кроме случаев, когда это необходимо для исполнения заказа или предусмотрено законодательством.

По запросу пользователя мы обновим, уточним или удалим сохраненные данные.
""".strip()
DEFAULT_METRIKA_CODE = "<!-- Яндекс.Метрика будет добавлена после получения реального идентификатора счетчика. -->"
DEFAULT_CONTACT_IMAGE_PATH = "catalog/assets/images/custom/step-gift.webp"
DEFAULT_CONTACT_IMAGE_ALT = "Подарок ручной работы от студии Подари момент"
DEFAULT_TELEGRAM_USERNAME = "molnia_cleaning_applications_bot"
DEFAULT_CONTACT_PHONE = "+7 (961) 490-58-39"


def load_payload() -> dict:
    for path in PRODUCT_DATA_FILES:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {"products": []}


def build_static_image_path(local_path: str | None) -> str:
    normalized = (local_path or "").replace("\\", "/").strip("/")
    if normalized.startswith("images/"):
        normalized = normalized[len("images/") :]
    if not normalized:
        return ""
    if (PRODUCT_IMAGES_DIR / normalized).is_file():
        return f"catalog/assets/images/products/{normalized}"
    return ""


def update_if_blank(instance, **values) -> bool:
    updated = False
    for field_name, value in values.items():
        current_value = getattr(instance, field_name)
        if current_value in ("", None):
            setattr(instance, field_name, value)
            updated = True
    return updated


def build_home_gallery_defaults() -> dict[str, str]:
    featured_services = list(Service.objects.filter(is_active=True).order_by("order", "pk")[:3])
    fallback_images = [
        ("catalog/assets/images/custom/hero-photo-2026-07-27.jpg", "Персональный подарок ручной работы"),
        ("catalog/assets/images/custom/hero-watercolor-alt.png", "Иллюстрация подарка Подари момент"),
        ("catalog/assets/images/custom/hero-watercolor-custom.png", "Творческая работа студии Подари момент"),
    ]

    defaults: dict[str, str] = {}
    for index in range(3):
        if index < len(featured_services):
            image_path = featured_services[index].main_image
            image_alt = featured_services[index].title
        else:
            image_path, image_alt = fallback_images[index]
        defaults[f"about_image_{index + 1}_path"] = image_path
        defaults[f"about_image_{index + 1}_alt"] = image_alt
    return defaults


@transaction.atomic
def ensure_default_content() -> None:
    site_settings, _ = SiteSettings.objects.get_or_create(
        pk=1,
        defaults={
            "site_name": "Подари момент",
            "brand_tagline": "Создаем моменты счастья",
            "phone": DEFAULT_CONTACT_PHONE,
            "email": "podary_moment@mail.ru",
            "application_email": "podary_moment@mail.ru",
            "telegram_username": DEFAULT_TELEGRAM_USERNAME,
            "whatsapp_phone": DEFAULT_CONTACT_PHONE,
            "max_url": "https://max.ru/podary-moment",
            "instagram_url": "https://www.instagram.com/studio_podarymoment?utm_source=qr&igsh=MXM3NHFjdXRrOHd0cw==",
            "logo_path": "catalog/assets/images/logo-mark.webp",
            "favicon_path": "catalog/assets/images/favicon.ico",
            "footer_description": "Создаем персональные подарки, которые сохраняют важные моменты и дарят радость.",
            "footer_promo": "Давайте создавать моменты счастья вместе!",
        },
    )
    if update_if_blank(
        site_settings,
        site_name="Подари момент",
        brand_tagline="Создаем моменты счастья",
        phone=DEFAULT_CONTACT_PHONE,
        email="podary_moment@mail.ru",
        application_email="podary_moment@mail.ru",
        telegram_username=DEFAULT_TELEGRAM_USERNAME,
        whatsapp_phone=DEFAULT_CONTACT_PHONE,
        max_url="https://max.ru/podary-moment",
        instagram_url="https://www.instagram.com/studio_podarymoment?utm_source=qr&igsh=MXM3NHFjdXRrOHd0cw==",
        logo_path="catalog/assets/images/logo-mark.webp",
        favicon_path="catalog/assets/images/favicon.ico",
        address="Онлайн-мастерская «Подари момент». Работаем по Москве и отправляем подарки по всей России.",
        work_time="Ежедневно: прием заявок с 09:00 до 21:00 по Москве.",
        policy_text=DEFAULT_SITE_POLICY_TEXT,
        metrika_code=DEFAULT_METRIKA_CODE,
    ):
        site_settings.save()

    if update_if_blank(
        site_settings,
        seo_title="Подари момент | Персональные подарки",
        seo_description="Персональные подарки, альбомы и творческие наборы Подари момент.",
        hero_title="Подари момент, который останется в памяти",
        hero_text="Создаем персональные раскраски, альбомы и подарки по вашему заказу с любовью к деталям.",
        hero_primary_text="Создать свой подарок",
        hero_primary_link="#contact",
        hero_secondary_text="Смотреть работы",
        hero_secondary_link="#works",
        hero_image_path="catalog/assets/images/custom/hero-watercolor-alt.png",
        hero_image_alt="Авторский подарочный альбом Подари момент",
        hero_advantages_text="\n".join(DEFAULT_HERO_ADVANTAGES),
        about_title="Создаем подарки, в которых живут важные моменты",
        about_lead="Подари момент превращает любимые фотографии, теплые истории и идеи в подарки, которые хочется хранить.",
        about_text="Мы создаем персональные раскраски, фотокниги и альбомы, творческие наборы, карточки и подарочные комплекты.",
        about_list="\n".join(
            [
                "Индивидуальный дизайн для вашей истории",
                "Продуманная комплектация и аккуратная подача",
                "Подарки для детей, семьи, друзей и особенных дат",
            ]
        ),
        catalog_title="Наши подарки",
        works_title="Наши работы",
        works_button_text="Смотреть больше работ",
        works_button_link="https://www.instagram.com/studio_podarymoment?utm_source=qr&igsh=MXM3NHFjdXRrOHd0cw==",
        reviews_title="Отзывы",
        process_title="Как мы работаем",
        contact_title="Создадим подарок специально для вас",
        contact_text="Оставьте заявку, и мы свяжемся с вами, чтобы обсудить все детали.",
        contact_success_message="Спасибо! Мы получили заявку и скоро свяжемся с вами.",
        footer_navigation_title="Навигация",
        footer_contacts_title="Контакты",
    ):
        site_settings.save()

    payload = load_payload()
    products = payload.get("products", [])

    for index, raw_product in enumerate(products, start=1):
        image_paths = [
            image_path
            for image_path in (
                build_static_image_path(image.get("local_path"))
                for image in raw_product.get("images", [])
            )
            if image_path
        ]
        first_image = image_paths[0] if image_paths else "catalog/assets/images/logo-mark.webp"
        title = (raw_product.get("title") or "").strip() or f"Подарок #{index}"
        description = (raw_product.get("description") or raw_product.get("contents") or "").strip()
        supplier_name = (raw_product.get("supplier_name") or "").strip()
        category = (raw_product.get("category") or "").strip()
        category_parent = (raw_product.get("category_parent") or "").strip()
        card_url = (raw_product.get("card_url") or "").strip()
        nm_id = raw_product.get("nm_id") or None
        defaults = {
            "order": index,
            "title": title,
            "description": description,
            "supplier_name": supplier_name,
            "category": category,
            "category_parent": category_parent,
            "card_url": card_url,
            "image_path": first_image,
            "extra_image_paths": image_paths[1:],
        }

        if nm_id is not None:
            service, created = Service.objects.get_or_create(nm_id=nm_id, defaults=defaults)
        else:
            service = Service.objects.filter(nm_id__isnull=True, title=title, card_url=card_url).first()
            if service is None:
                service = Service.objects.create(**defaults)
                created = True
            else:
                created = False

        if not created:
            changed = update_if_blank(
                service,
                title=title,
                description=description,
                supplier_name=supplier_name,
                category=category,
                category_parent=category_parent,
                card_url=card_url,
                image_path=first_image,
            )
            if not service.extra_image_paths and image_paths[1:]:
                service.extra_image_paths = image_paths[1:]
                changed = True
            if changed:
                service.save()

    home_media_defaults = build_home_gallery_defaults()
    if update_if_blank(
        site_settings,
        **home_media_defaults,
        contact_image_path=DEFAULT_CONTACT_IMAGE_PATH,
        contact_image_alt=DEFAULT_CONTACT_IMAGE_ALT,
    ):
        site_settings.save()

    if not WorkExample.objects.exists():
        home_services = list(Service.objects.filter(is_active=True).order_by("order", "pk")[:8])
        for order, service in enumerate(home_services, start=1):
            WorkExample.objects.create(
                order=order,
                title=service.title,
                image_path=service.main_image,
                alt=service.title,
                description=service.description[:240],
                show_on_home=True,
            )

    if not Step.objects.exists():
        for order, (title, description, icon_path) in enumerate(DEFAULT_STEPS, start=1):
            Step.objects.create(order=order, title=title, description=description, icon_path=icon_path, is_active=True)

    if not Review.objects.exists():
        for order, (rating, text) in enumerate(DEFAULT_REVIEWS, start=1):
            Review.objects.create(order=order, rating=rating, text=text, is_active=True)
