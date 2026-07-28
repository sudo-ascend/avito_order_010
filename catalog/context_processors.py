from __future__ import annotations

from .default_content import ensure_default_content
from .models import SiteSettings


def site_context(request):
    ensure_default_content()
    site_settings = SiteSettings.objects.first()
    return {
        "site_settings": site_settings,
        "home_settings": site_settings,
    }
