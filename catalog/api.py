from __future__ import annotations

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import ApplicationForm
from .models import SiteSettings
from .utils import notify_application

DEFAULT_SUCCESS_MESSAGE = "Спасибо! Заявка отправлена, мы скоро свяжемся с вами."
DEFAULT_INVALID_MESSAGE = "Пожалуйста, проверьте форму."


def build_form_errors(form: ApplicationForm) -> dict[str, list[str]]:
    return {
        field_name: [item["message"] for item in items]
        for field_name, items in form.errors.get_json_data(escape_html=True).items()
    }


def get_client_ip(request) -> str | None:
    forwarded_for = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    return forwarded_for or request.META.get("REMOTE_ADDR")


def save_application_from_request(form: ApplicationForm, request):
    application = form.save(commit=False)
    application.source = "website"
    application.ip_address = get_client_ip(request)
    application.user_agent = request.META.get("HTTP_USER_AGENT", "")
    application.save()
    return application


@require_POST
def application_create_api(request):
    form = ApplicationForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": DEFAULT_INVALID_MESSAGE,
                "errors": build_form_errors(form),
            },
            status=400,
        )

    application = save_application_from_request(form, request)
    site_settings = SiteSettings.objects.first()
    notify_application(application, site_settings)

    success_message = (
        SiteSettings.objects.values_list("contact_success_message", flat=True).first() or DEFAULT_SUCCESS_MESSAGE
    )
    return JsonResponse(
        {
            "ok": True,
            "message": success_message,
        },
        status=201,
    )
