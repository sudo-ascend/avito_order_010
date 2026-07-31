from __future__ import annotations

import json
from urllib.parse import urljoin

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

from .models import Service, SiteSettings

DEFAULT_HOME_TITLE = "Персональные подарки на заказ в Москве и по России | Подари момент"
DEFAULT_HOME_DESCRIPTION = (
    "Авторские подарки на заказ: фотокниги, творческие наборы и памятные сюрпризы. "
    "Индивидуальный дизайн, ручная работа и доставка по России."
)
DEFAULT_SITE_KEYWORDS = (
    "персональные подарки на заказ, авторские подарки, подарки ручной работы, "
    "подарки с фотографиями, фотокниги на заказ, подарки для детей, подарки для семьи, "
    "подарки с доставкой по россии"
)
INDEX_ROBOTS = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
NOINDEX_ROBOTS = "noindex,nofollow,noarchive,max-snippet:0,max-image-preview:none,max-video-preview:0"


def normalize_text(value: str) -> str:
    return " ".join((value or "").split())


def trim_text(value: str, limit: int) -> str:
    cleaned = normalize_text(value)
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[: limit - 1].rsplit(" ", 1)[0].rstrip(",.- ")
    return f"{shortened}..."


def base_url(request=None) -> str:
    if settings.SITE_URL:
        return settings.SITE_URL
    if request is None:
        return ""
    return f"{request.scheme}://{request.get_host()}".rstrip("/")


def absolute_url(request, value: str) -> str:
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    path = value if value.startswith("/") else static(value)
    return urljoin(f"{base_url(request)}/", path.lstrip("/"))


def canonical_url(request) -> str:
    return urljoin(f"{base_url(request)}/", request.path.lstrip("/"))


def site_name(site_settings: SiteSettings | None) -> str:
    if site_settings and site_settings.site_name:
        return site_settings.site_name
    return "Подари момент"


def default_share_title(site_settings: SiteSettings | None) -> str:
    return trim_text(
        getattr(site_settings, "share_title", "") or DEFAULT_HOME_TITLE,
        110,
    )


def default_share_description(site_settings: SiteSettings | None) -> str:
    source = getattr(site_settings, "share_description", "") or DEFAULT_HOME_DESCRIPTION
    return trim_text(source, 220)


def default_share_image(request, site_settings: SiteSettings | None) -> str:
    if not site_settings:
        return ""
    image_path = site_settings.share_image_path or site_settings.hero_image_path or site_settings.logo_path
    return absolute_url(request, image_path)


def default_share_image_alt(site_settings: SiteSettings | None) -> str:
    if not site_settings:
        return "Превью ссылки"
    return site_settings.share_image_alt or site_name(site_settings)


def build_keywords(extra_terms: list[str] | None = None) -> str:
    items = [DEFAULT_SITE_KEYWORDS]
    items.extend(term for term in (extra_terms or []) if term)
    return ", ".join(dict.fromkeys(items))


def json_ld(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def organization_schema(request, site_settings: SiteSettings | None) -> dict:
    name = site_name(site_settings)
    data: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{base_url(request)}/#organization",
        "name": name,
        "url": base_url(request),
        "logo": absolute_url(request, getattr(site_settings, "logo_path", "")),
        "image": default_share_image(request, site_settings),
        "description": DEFAULT_HOME_DESCRIPTION,
        "inLanguage": "ru-RU",
        "areaServed": "RU",
    }
    same_as = [
        url
        for url in (
            getattr(site_settings, "instagram_url", ""),
            getattr(site_settings, "telegram_url", ""),
            getattr(site_settings, "whatsapp_url", ""),
            getattr(site_settings, "max_url", ""),
        )
        if url
    ]
    if same_as:
        data["sameAs"] = same_as
    contact_point = {}
    if getattr(site_settings, "phone", ""):
        contact_point["telephone"] = site_settings.phone
    if getattr(site_settings, "email", ""):
        contact_point["email"] = site_settings.email
    if contact_point:
        contact_point.update(
            {
                "@type": "ContactPoint",
                "contactType": "customer support",
                "availableLanguage": ["ru"],
            }
        )
        data["contactPoint"] = [contact_point]
    if getattr(site_settings, "address", ""):
        data["address"] = site_settings.address
    return data


def website_schema(request, site_settings: SiteSettings | None) -> dict:
    name = site_name(site_settings)
    url = urljoin(f"{base_url(request)}/", reverse("catalog:index").lstrip("/"))
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{url}#website",
        "url": url,
        "name": name,
        "publisher": {"@id": f"{base_url(request)}/#organization"},
        "inLanguage": "ru-RU",
    }


def home_collection_schema(request, site_settings: SiteSettings | None) -> dict:
    url = urljoin(f"{base_url(request)}/", reverse("catalog:index").lstrip("/"))
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": f"{url}#webpage",
        "url": url,
        "name": DEFAULT_HOME_TITLE,
        "description": DEFAULT_HOME_DESCRIPTION,
        "isPartOf": {"@id": f"{url}#website"},
        "about": {"@id": f"{base_url(request)}/#organization"},
        "inLanguage": "ru-RU",
    }


def home_item_list_schema(request, services: list[Service]) -> dict:
    elements = []
    for index, service in enumerate(services[:12], start=1):
        elements.append(
            {
                "@type": "ListItem",
                "position": index,
                "url": absolute_url(request, reverse("catalog:product_detail", args=[service.pk])),
                "name": service.title,
            }
        )
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Каталог подарков",
        "itemListElement": elements,
    }


def breadcrumb_schema(request, service: Service) -> dict:
    home_url = absolute_url(request, reverse("catalog:index"))
    product_url = absolute_url(request, reverse("catalog:product_detail", args=[service.pk]))
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Главная",
                "item": home_url,
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": service.title,
                "item": product_url,
            },
        ],
    }


def product_schema(request, site_settings: SiteSettings | None, service: Service) -> dict:
    images = [
        absolute_url(request, path)
        for path in [service.main_image, *[path for path in service.extra_image_paths if path]]
        if path
    ]
    description = trim_text(
        service.description
        or f"{service.title}. Авторский подарок на заказ от студии {site_name(site_settings)}.",
        500,
    )
    data: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": f"{absolute_url(request, reverse('catalog:product_detail', args=[service.pk]))}#product",
        "name": service.title,
        "url": absolute_url(request, reverse("catalog:product_detail", args=[service.pk])),
        "description": description,
        "image": images,
        "brand": {
            "@type": "Brand",
            "name": site_name(site_settings),
        },
        "category": service.category_parent or service.category,
    }
    if service.nm_id:
        data["sku"] = str(service.nm_id)
        data["mpn"] = str(service.nm_id)
    return data


def build_home_seo(request, site_settings: SiteSettings | None, services: list[Service]) -> dict[str, object]:
    share_title = default_share_title(site_settings)
    share_description = default_share_description(site_settings)
    share_image = default_share_image(request, site_settings)
    share_image_alt = default_share_image_alt(site_settings)
    url = canonical_url(request)
    return {
        "title": DEFAULT_HOME_TITLE,
        "description": DEFAULT_HOME_DESCRIPTION,
        "keywords": build_keywords(["подарки в москве", "подарки по россии"]),
        "canonical_url": url,
        "robots": INDEX_ROBOTS,
        "googlebot": INDEX_ROBOTS,
        "og_type": "website",
        "og_site_name": site_name(site_settings),
        "og_title": share_title,
        "og_description": share_description,
        "og_url": url,
        "og_image": share_image,
        "og_image_alt": share_image_alt,
        "twitter_card": "summary_large_image" if share_image else "summary",
        "twitter_title": share_title,
        "twitter_description": share_description,
        "twitter_image": share_image,
        "twitter_image_alt": share_image_alt,
        "structured_data": [
            json_ld(organization_schema(request, site_settings)),
            json_ld(website_schema(request, site_settings)),
            json_ld(home_collection_schema(request, site_settings)),
            json_ld(home_item_list_schema(request, services)),
        ],
    }


def build_product_seo(request, site_settings: SiteSettings | None, service: Service) -> dict[str, object]:
    product_url = canonical_url(request)
    product_title = trim_text(f"{service.title} на заказ | {site_name(site_settings)}", 70)
    product_description = trim_text(
        service.description
        or f"{service.title}. Персональный подарок на заказ от студии {site_name(site_settings)} "
        "с аккуратной упаковкой и доставкой по России.",
        170,
    )
    image_url = absolute_url(request, service.main_image)
    image_alt = service.title
    return {
        "title": product_title,
        "description": product_description,
        "keywords": build_keywords([service.title, service.category_parent, service.category]),
        "canonical_url": product_url,
        "robots": INDEX_ROBOTS,
        "googlebot": INDEX_ROBOTS,
        "og_type": "product",
        "og_site_name": site_name(site_settings),
        "og_title": product_title,
        "og_description": product_description,
        "og_url": product_url,
        "og_image": image_url or default_share_image(request, site_settings),
        "og_image_alt": image_alt or default_share_image_alt(site_settings),
        "twitter_card": "summary_large_image" if image_url else "summary",
        "twitter_title": product_title,
        "twitter_description": product_description,
        "twitter_image": image_url or default_share_image(request, site_settings),
        "twitter_image_alt": image_alt or default_share_image_alt(site_settings),
        "structured_data": [
            json_ld(organization_schema(request, site_settings)),
            json_ld(website_schema(request, site_settings)),
            json_ld(breadcrumb_schema(request, service)),
            json_ld(product_schema(request, site_settings, service)),
        ],
    }


def build_error_seo() -> dict[str, str]:
    return {
        "robots": NOINDEX_ROBOTS,
    }
