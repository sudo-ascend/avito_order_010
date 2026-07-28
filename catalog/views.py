from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .api import save_application_from_request
from .default_content import ensure_default_content
from .forms import ApplicationForm
from .models import Review, Service, SiteSettings, Step, WorkExample
from .utils import notify_application


def _shorten(text, limit=140):
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[: limit - 1].rsplit(" ", 1)[0]
    return f"{truncated}..."


def _build_home_context(form: ApplicationForm | None = None):
    ensure_default_content()
    site_settings = SiteSettings.objects.first()
    home_settings = site_settings
    products_qs = Service.objects.filter(is_active=True).order_by("category_parent", "category", "order", "pk")
    products = [
        {
            "nm_id": product.nm_id,
            "title": product.title,
            "category": product.category,
            "category_parent": product.category_parent,
            "description": _shorten(product.description),
            "supplier_name": product.supplier_name,
            "main_image": product.main_image,
            "images": [product.main_image, *product.extra_image_paths],
        }
        for product in products_qs
    ]
    gallery_images = [
        {"src": item.image_path, "alt": item.alt or item.title}
        for item in WorkExample.objects.filter(show_on_home=True).order_by("order", "pk")
    ]
    if not gallery_images:
        gallery_images = [{"src": product["main_image"], "alt": product["title"]} for product in products[:8]]
    about_images = []
    about_image_fallback_alt = "Примеры подарков"
    if home_settings and home_settings.about_title:
        about_image_fallback_alt = home_settings.about_title
    elif site_settings and site_settings.site_name:
        about_image_fallback_alt = site_settings.site_name
    if home_settings:
        for index in range(1, 4):
            image_path = getattr(home_settings, f"about_image_{index}_path", "")
            image_alt = getattr(home_settings, f"about_image_{index}_alt", "")
            if image_path:
                about_images.append({"src": image_path, "alt": image_alt or about_image_fallback_alt})
    if not about_images:
        about_images = [{"src": product["main_image"], "alt": product["title"]} for product in products[:3]]

    return {
        "site_settings": site_settings,
        "home_settings": home_settings,
        "brand_name": site_settings.site_name if site_settings else "Подари момент",
        "products": products,
        "gallery_images": gallery_images,
        "about_images": about_images,
        "reviews": Review.objects.filter(is_active=True).order_by("order", "pk"),
        "steps": Step.objects.filter(is_active=True).order_by("order", "pk"),
        "application_form": form or ApplicationForm(),
        "current_year": datetime.now(ZoneInfo("Europe/Moscow")).year,
    }


def index(request):
    context = _build_home_context()
    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = save_application_from_request(form, request)
            notify_application(application, context["site_settings"])
            success_message = (
                context["home_settings"].contact_success_message
                if context["home_settings"]
                else "Спасибо! Мы получили заявку и скоро свяжемся с вами."
            )
            messages.success(request, success_message)
            return redirect(f"{reverse('catalog:index')}#contact")

        context = _build_home_context(form=form)
        return render(request, "catalog/index.html", context)

    return render(request, "catalog/index.html", context)


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
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
