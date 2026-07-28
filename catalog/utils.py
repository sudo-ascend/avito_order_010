from __future__ import annotations

import html
import logging
import re

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import TelegramSubscriber

logger = logging.getLogger(__name__)

APPLICATION_EMAIL_SUBJECT = "Новая заявка с сайта"
TELEGRAM_SUBSCRIBED_MESSAGE = "Вы подписались на уведомления о новых заявках."
TELEGRAM_UNSUBSCRIBED_MESSAGE = "Вы отписались от уведомлений о новых заявках."


def clean_phone_number(raw_phone: str) -> str | None:
    digits = re.sub(r"\D+", "", raw_phone or "")
    if digits.startswith("8"):
        digits = f"7{digits[1:]}"
    elif len(digits) == 10:
        digits = f"7{digits}"

    if len(digits) != 11 or not digits.startswith("7"):
        return None
    return f"+{digits}"


def format_phone_display(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone)
    if len(digits) != 11:
        return phone
    return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


def phone_href(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone or "")
    return f"tel:+{digits}" if digits else "tel:"


def build_application_message(application) -> str:
    parts = [
        APPLICATION_EMAIL_SUBJECT,
        f"Имя: {application.name}",
        f"Телефон: {application.phone}",
        f"Email: {application.email or 'Не указан'}",
        f"Товар: {application.service_title or 'Не указан'}",
        f"Время: {application.created_at:%d.%m.%Y %H:%M}",
    ]
    if application.comment:
        parts.append(f"Комментарий: {application.comment}")
    return "\n".join(parts)


def build_application_telegram_message(application) -> str:
    service_title = html.escape(application.service_title or "Не указан")
    phone = html.escape(clean_phone_number(application.phone) or application.phone)
    parts = [
        f"<b>{html.escape(APPLICATION_EMAIL_SUBJECT)}</b>",
        f"<b>Имя:</b> {html.escape(application.name)}",
        f"<b>Телефон:</b> <code>{phone}</code>",
        f"<b>Email:</b> {html.escape(application.email or 'Не указан')}",
        f"<b>Товар:</b> {service_title}",
        f"<b>Время:</b> {application.created_at:%d.%m.%Y %H:%M}",
    ]
    if application.comment:
        parts.append(f"<b>Комментарий:</b> {html.escape(application.comment)}")
    return "\n".join(parts)


def build_application_email_context(application, site_settings=None) -> dict:
    return {
        "site_name": getattr(settings, "SITE_NAME", "Подари момент"),
        "title": APPLICATION_EMAIL_SUBJECT,
        "subtitle": "На сайте оставили новую заявку.",
        "details": [
            {"label": "Имя", "value": application.name},
            {"label": "Телефон", "value": application.phone, "href": phone_href(application.phone)},
            {"label": "Email", "value": application.email or "Не указан"},
            {"label": "Товар", "value": application.service_title or "Не указан"},
            {"label": "Время", "value": f"{application.created_at:%d.%m.%Y %H:%M}"},
        ],
        "comment": application.comment,
        "contact_phone": getattr(site_settings, "phone", ""),
        "contact_email": getattr(site_settings, "email", ""),
    }


def send_application_email(application, recipient_email: str, site_settings=None) -> None:
    text_body = build_application_message(application)
    html_body = render_to_string(
        "emails/application_notification.html",
        build_application_email_context(application, site_settings),
    )
    message = EmailMultiAlternatives(
        subject=APPLICATION_EMAIL_SUBJECT,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


def send_telegram_message(text: str, chat_id: str | None = None) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    actual_chat_id = chat_id or settings.TELEGRAM_CHAT_ID
    if not token or not actual_chat_id:
        return False

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": actual_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        },
        timeout=10,
    )
    response.raise_for_status()
    return True


def upsert_telegram_subscriber(chat_data: dict, *, is_active: bool) -> TelegramSubscriber | None:
    chat_id = chat_data.get("id")
    if chat_id is None:
        return None

    subscriber, _ = TelegramSubscriber.objects.update_or_create(
        chat_id=str(chat_id),
        defaults={
            "username": (chat_data.get("username") or "")[:255],
            "first_name": (chat_data.get("first_name") or "")[:255],
            "last_name": (chat_data.get("last_name") or "")[:255],
            "is_active": is_active,
        },
    )
    return subscriber


def send_telegram_notification_to_subscribers(text: str) -> bool:
    subscribers = list(TelegramSubscriber.objects.filter(is_active=True).values_list("chat_id", flat=True))
    if not subscribers:
        return False

    delivered = False
    for subscriber_chat_id in subscribers:
        try:
            delivered = send_telegram_message(text, subscriber_chat_id) or delivered
        except Exception:
            logger.exception("Не удалось отправить Telegram подписчику %s", subscriber_chat_id)
    return delivered


def email_notifications_enabled() -> bool:
    backend = getattr(settings, "EMAIL_BACKEND", "")
    if backend != "django.core.mail.backends.smtp.EmailBackend":
        return True
    return bool(getattr(settings, "EMAIL_HOST", ""))


def notify_application(application, site_settings=None) -> dict[str, bool]:
    recipient_email = getattr(site_settings, "application_email", "") or settings.APPLICATION_NOTIFICATION_EMAIL
    result = {"email": False, "telegram": False}

    try:
        if recipient_email and email_notifications_enabled():
            send_application_email(application, recipient_email, site_settings)
            result["email"] = True
    except Exception:
        logger.exception("Не удалось отправить email по заявке %s", application.pk)

    try:
        result["telegram"] = send_telegram_notification_to_subscribers(build_application_telegram_message(application))
    except Exception:
        logger.exception("Не удалось отправить Telegram по заявке %s", application.pk)

    return result
