from __future__ import annotations

import re

from django.db import models


def parse_text_items(value: str) -> list[str]:
    if not value:
        return []
    normalized = value.replace(",", "\n")
    return [item.strip(" -\t") for item in normalized.splitlines() if item.strip()]


HERO_BENEFIT_ICONS = ("heart", "brush", "spark", "truck", "home")


class SiteSettings(models.Model):
    site_name = models.CharField("Название сайта", max_length=255, default="Подари момент")
    brand_tagline = models.CharField("Подзаголовок бренда", max_length=255, blank=True, default="Создаем моменты счастья")
    phone = models.CharField("Телефон", max_length=32, blank=True)
    email = models.EmailField("Email", blank=True)
    telegram_username = models.CharField("Telegram username", max_length=128, blank=True)
    whatsapp_phone = models.CharField("WhatsApp", max_length=32, blank=True)
    max_url = models.URLField("Max URL", blank=True)
    instagram_url = models.URLField("Instagram URL", blank=True)
    application_email = models.EmailField("Email для заявок", blank=True)
    address = models.TextField("Адрес", blank=True)
    work_time = models.CharField("Режим работы", max_length=128, blank=True)
    logo_path = models.CharField("Путь к логотипу", max_length=255, blank=True, default="catalog/assets/images/logo-mark.webp")
    favicon_path = models.CharField("Путь к favicon", max_length=255, blank=True, default="catalog/assets/images/favicon.ico")
    footer_description = models.TextField("Описание в футере", blank=True)
    footer_promo = models.TextField("Промо-текст в футере", blank=True)
    metrika_code = models.TextField("Код Яндекс.Метрики", blank=True)
    policy_text = models.TextField("Текст политики", blank=True)
    seo_title = models.CharField("SEO title главной", max_length=255, blank=True)
    seo_description = models.TextField("SEO description главной", blank=True)
    hero_title = models.CharField("Заголовок hero", max_length=255, default="Подари момент, который останется в памяти")
    hero_text = models.TextField("Текст hero", blank=True)
    hero_primary_text = models.CharField("Текст основной кнопки hero", max_length=120, default="Создать свой подарок")
    hero_primary_link = models.CharField("Ссылка основной кнопки hero", max_length=255, default="#contact")
    hero_secondary_text = models.CharField("Текст второй кнопки hero", max_length=120, default="Смотреть работы")
    hero_secondary_link = models.CharField("Ссылка второй кнопки hero", max_length=255, default="#works")
    hero_image_path = models.CharField("Путь к hero-изображению", max_length=255, blank=True)
    hero_image_alt = models.CharField("Alt hero-изображения", max_length=255, blank=True)
    hero_advantages_text = models.TextField("Преимущества hero", blank=True)
    about_title = models.CharField("Заголовок блока о нас", max_length=255, blank=True)
    about_lead = models.TextField("Лид блока о нас", blank=True)
    about_text = models.TextField("Основной текст блока о нас", blank=True)
    about_list = models.TextField("Список в блоке о нас", blank=True)
    about_image_1_path = models.CharField("Путь к первой картинке блока о нас", max_length=255, blank=True)
    about_image_1_alt = models.CharField("Alt первой картинки блока о нас", max_length=255, blank=True)
    about_image_2_path = models.CharField("Путь ко второй картинке блока о нас", max_length=255, blank=True)
    about_image_2_alt = models.CharField("Alt второй картинки блока о нас", max_length=255, blank=True)
    about_image_3_path = models.CharField("Путь к третьей картинке блока о нас", max_length=255, blank=True)
    about_image_3_alt = models.CharField("Alt третьей картинки блока о нас", max_length=255, blank=True)
    catalog_title = models.CharField("Заголовок каталога", max_length=255, default="Наши подарки")
    works_title = models.CharField("Заголовок работ", max_length=255, default="Наши работы")
    works_button_text = models.CharField("Текст кнопки работ", max_length=120, default="Смотреть больше работ")
    works_button_link = models.CharField("Ссылка кнопки работ", max_length=255, blank=True)
    reviews_title = models.CharField("Заголовок отзывов", max_length=255, default="Отзывы")
    process_title = models.CharField("Заголовок процесса", max_length=255, default="Как мы работаем")
    contact_title = models.CharField("Заголовок контактов", max_length=255, default="Создадим подарок специально для вас")
    contact_text = models.TextField("Текст блока контактов", blank=True)
    contact_image_path = models.CharField("Путь к картинке блока контактов", max_length=255, blank=True)
    contact_image_alt = models.CharField("Alt картинки блока контактов", max_length=255, blank=True)
    contact_success_message = models.CharField(
        "Сообщение об успешной отправке",
        max_length=255,
        default="Спасибо! Мы получили заявку и скоро свяжемся с вами.",
    )
    footer_navigation_title = models.CharField("Заголовок навигации в футере", max_length=120, default="Навигация")
    footer_contacts_title = models.CharField("Заголовок контактов в футере", max_length=120, default="Контакты")
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self) -> str:
        return self.site_name or "Настройки сайта"

    @property
    def phone_href(self) -> str:
        digits = "".join(char for char in self.phone if char.isdigit())
        return f"tel:+{digits}" if digits else "tel:"

    @property
    def telegram_handle(self) -> str:
        username = self.telegram_username.strip().lstrip("@")
        return f"@{username}" if username else ""

    @property
    def telegram_url(self) -> str:
        username = self.telegram_username.strip().lstrip("@")
        return f"https://t.me/{username}" if username else ""

    @property
    def whatsapp_url(self) -> str:
        digits = re.sub(r"\D+", "", self.whatsapp_phone or "")
        if digits.startswith("8"):
            digits = f"7{digits[1:]}"
        elif len(digits) == 10:
            digits = f"7{digits}"
        return f"https://wa.me/{digits}" if digits else ""

    @property
    def about_list_items(self) -> list[str]:
        return parse_text_items(self.about_list)

    @property
    def hero_advantages(self) -> list[dict[str, str]]:
        advantages = []
        for index, item in enumerate(parse_text_items(self.hero_advantages_text)):
            icon = HERO_BENEFIT_ICONS[index] if index < len(HERO_BENEFIT_ICONS) else "check"
            advantages.append({"title": item, "icon": icon})
        return advantages


class TelegramSubscriber(models.Model):
    chat_id = models.CharField("Telegram chat ID", max_length=128, unique=True)
    username = models.CharField("Username", max_length=255, blank=True)
    first_name = models.CharField("Имя", max_length=255, blank=True)
    last_name = models.CharField("Фамилия", max_length=255, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    subscribed_at = models.DateTimeField("Подписан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Подписчик Telegram"
        verbose_name_plural = "Подписчики Telegram"
        ordering = ("-updated_at", "-pk")

    def __str__(self) -> str:
        label = self.username or " ".join(part for part in (self.first_name, self.last_name) if part).strip()
        return label or self.chat_id


class OrderedModel(models.Model):
    order = models.PositiveIntegerField("Порядок", default=10)

    class Meta:
        abstract = True
        ordering = ("order", "pk")


class Service(OrderedModel):
    nm_id = models.PositiveBigIntegerField("NM ID", blank=True, null=True, unique=True)
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    supplier_name = models.CharField("Поставщик", max_length=255, blank=True)
    category = models.CharField("Категория", max_length=255, blank=True)
    category_parent = models.CharField("Родительская категория", max_length=255, blank=True)
    card_url = models.URLField("Ссылка на карточку", blank=True)
    image_path = models.CharField("Путь к изображению", max_length=255, blank=True)
    extra_image_paths = models.JSONField("Дополнительные изображения", blank=True, default=list)
    is_active = models.BooleanField("Товар активен", default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Товар каталога"
        verbose_name_plural = "Товары каталога"

    def __str__(self) -> str:
        return self.title

    @property
    def main_image(self) -> str:
        return self.image_path or "catalog/assets/images/logo-mark.webp"


class WorkExample(OrderedModel):
    title = models.CharField("Название", max_length=255, blank=True)
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        related_name="work_examples",
        verbose_name="Товар для перехода",
        blank=True,
        null=True,
    )
    image_path = models.CharField("Путь к изображению", max_length=255)
    alt = models.CharField("Alt изображения", max_length=255, blank=True)
    description = models.TextField("Описание", blank=True)
    show_on_home = models.BooleanField("Показывать на главной", default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Пример работы"
        verbose_name_plural = "Примеры работ"

    def __str__(self) -> str:
        return self.title or self.alt or f"Пример #{self.pk}"


class Step(OrderedModel):
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    icon_path = models.CharField("Путь к иконке", max_length=255, blank=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Этап"
        verbose_name_plural = "Этапы"

    def __str__(self) -> str:
        return self.title


class Review(OrderedModel):
    rating = models.PositiveSmallIntegerField("Оценка", default=5)
    text = models.TextField("Текст")
    is_active = models.BooleanField("Активен", default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self) -> str:
        return f"{self.rating}/5 - {self.text[:50]}"


class Application(models.Model):
    STATUS_NEW = "new"
    STATUS_PROCESSED = "processed"
    STATUS_SPAM = "spam"
    STATUS_CHOICES = (
        (STATUS_NEW, "Новая"),
        (STATUS_PROCESSED, "Обработана"),
        (STATUS_SPAM, "Спам"),
    )

    name = models.CharField("Имя", max_length=255)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Email", blank=True)
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name="Товар",
        blank=True,
        null=True,
    )
    comment = models.TextField("Комментарий", blank=True)
    consent = models.BooleanField("Согласие на обработку данных", default=False)
    status = models.CharField("Статус", max_length=16, choices=STATUS_CHOICES, default=STATUS_NEW)
    source = models.CharField("Источник", max_length=64, blank=True, default="website")
    ip_address = models.GenericIPAddressField("IP-адрес", blank=True, null=True)
    user_agent = models.TextField("User-Agent", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ("-created_at",)

    @property
    def service_title(self) -> str:
        return self.service.title if self.service_id else ""

    def __str__(self) -> str:
        service_title = self.service_title or "Без товара"
        return f"{self.name} - {service_title}"
