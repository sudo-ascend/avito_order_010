from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .api import save_application_from_request
from .default_content import ensure_default_content
from .forms import ApplicationForm
from .models import Review, Service, SiteSettings, Step, WorkExample
from .seo import absolute_url, build_home_seo, build_product_seo
from .utils import notify_application

DEFAULT_SUCCESS_MESSAGE = "Создаем моменты счастья"


def _normalize_text(text: str) -> str:
    return " ".join((text or "").split())


def _shorten(text: str, limit: int = 140) -> str:
    cleaned = _normalize_text(text)
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[: limit - 1].rsplit(" ", 1)[0]
    return f"{truncated}..."


def _service_detail_url(service: Service) -> str:
    return reverse("catalog:product_detail", args=[service.pk])


def _serialize_service(service: Service, *, shorten_description: bool = True) -> dict[str, object]:
    images = [service.main_image, *[path for path in service.extra_image_paths if path]]
    description = _shorten(service.description) if shorten_description else _normalize_text(service.description)
    return {
        "pk": service.pk,
        "nm_id": service.nm_id,
        "title": service.title,
        "category": service.category,
        "category_parent": service.category_parent,
        "description": description,
        "supplier_name": service.supplier_name,
        "main_image": images[0],
        "images": images,
        "card_url": service.card_url,
        "detail_url": _service_detail_url(service),
    }


def _base_context(request, form: ApplicationForm | None = None) -> dict[str, object]:
    ensure_default_content()
    site_settings = SiteSettings.objects.first()
    home_settings = site_settings
    return {
        "site_settings": site_settings,
        "home_settings": home_settings,
        "brand_name": site_settings.site_name if site_settings else "Подари момент",
        "application_form": form or ApplicationForm(),
        "current_year": datetime.now(ZoneInfo("Europe/Moscow")).year,
        "site_base_url": absolute_url(request, "/"),
    }


def _build_gallery_images(services: list[Service], products: list[dict[str, object]]) -> list[dict[str, str]]:
    work_examples = list(WorkExample.objects.filter(show_on_home=True).select_related("service").order_by("order", "pk"))
    if not work_examples:
        return [
            {"src": product["main_image"], "alt": product["title"], "detail_url": product["detail_url"]}
            for product in products[:8]
        ]

    gallery_images: list[dict[str, str]] = []
    for index, item in enumerate(work_examples):
        linked_service = None
        if item.service_id and item.service and item.service.is_active:
            linked_service = item.service
        elif services:
            linked_service = services[index % len(services)]

        gallery_images.append(
            {
                "src": item.image_path,
                "alt": item.alt or item.title,
                "detail_url": _service_detail_url(linked_service) if linked_service else "",
            }
        )
    return gallery_images


def _build_home_context(request, form: ApplicationForm | None = None) -> dict[str, object]:
    context = _base_context(request, form=form)
    services_by_catalog = list(Service.objects.filter(is_active=True).order_by("category_parent", "category", "order", "pk"))
    services_by_order = list(Service.objects.filter(is_active=True).order_by("order", "pk"))
    products = [_serialize_service(service) for service in services_by_catalog]
    about_products = [_serialize_service(service) for service in services_by_order]

    home_settings = context["home_settings"]
    about_images = []
    about_image_fallback_alt = "Примеры подарков"
    if home_settings and home_settings.about_title:
        about_image_fallback_alt = home_settings.about_title
    elif context["site_settings"] and context["site_settings"].site_name:
        about_image_fallback_alt = context["site_settings"].site_name

    if home_settings:
        for index in range(1, 4):
            image_path = getattr(home_settings, f"about_image_{index}_path", "")
            image_alt = getattr(home_settings, f"about_image_{index}_alt", "")
            if image_path:
                about_images.append({"src": image_path, "alt": image_alt or about_image_fallback_alt})

    if not about_images:
        about_images = [{"src": product["main_image"], "alt": product["title"]} for product in products[:3]]

    context.update(
        {
            "products": products,
            "about_products": about_products,
            "gallery_images": _build_gallery_images(services_by_order, products),
            "about_images": about_images,
            "reviews": Review.objects.filter(is_active=True).order_by("order", "pk"),
            "steps": Step.objects.filter(is_active=True).order_by("order", "pk"),
            "seo": build_home_seo(request, context["site_settings"], services_by_order),
        }
    )
    return context


def _build_product_detail_context(request, service: Service, form: ApplicationForm | None = None) -> dict[str, object]:
    context = _base_context(request, form=form or ApplicationForm(initial={"service": service.pk}))
    related_products = [
        _serialize_service(item)
        for item in Service.objects.filter(is_active=True).exclude(pk=service.pk).order_by("order", "pk")[:4]
    ]
    context.update(
        {
            "product": _serialize_service(service, shorten_description=False),
            "related_products": related_products,
            "seo": build_product_seo(request, context["site_settings"], service),
        }
    )
    return context


def _contact_success_message(home_settings: SiteSettings | None) -> str:
    if home_settings and home_settings.contact_success_message:
        return home_settings.contact_success_message
    return DEFAULT_SUCCESS_MESSAGE


def index(request):
    context = _build_home_context(request)
    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = save_application_from_request(form, request)
            notify_application(application, context["site_settings"])
            messages.success(request, _contact_success_message(context["home_settings"]))
            return redirect(f"{reverse('catalog:index')}#contact")

        context = _build_home_context(request, form=form)
        return render(request, "catalog/index.html", context)

    return render(request, "catalog/index.html", context)


def product_detail(request, pk: int):
    service = get_object_or_404(Service.objects.filter(is_active=True), pk=pk)
    context = _build_product_detail_context(request, service)

    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = save_application_from_request(form, request)
            notify_application(application, context["site_settings"])
            messages.success(request, _contact_success_message(context["home_settings"]))
            return redirect(f"{reverse('catalog:product_detail', args=[service.pk])}#contact")

        context = _build_product_detail_context(request, service, form=form)
        return render(request, "catalog/product_detail.html", context)

    return render(request, "catalog/product_detail.html", context)


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /api/",
        f"Sitemap: {absolute_url(request, reverse('django.contrib.sitemaps.views.sitemap'))}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def csrf_failure(request, reason=""):
    return render(request, "error_pages/403_csrf.html", {"reason": reason}, status=403)


def bad_request(request, exception):
    return render(request, "error_pages/400.html", status=400)


def permission_denied(request, exception):
    return render(request, "error_pages/403.html", status=403)


def page_not_found(request, exception):
    return render(request, "error_pages/404.html", status=404)


def server_error(request):
    return render(request, "error_pages/500.html", status=500)
