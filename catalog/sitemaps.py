from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Service, SiteSettings


class HomeSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def items(self):
        return ["home"]

    def location(self, item):
        return reverse("catalog:index")

    def lastmod(self, item):
        return SiteSettings.objects.values_list("updated_at", flat=True).first()


class ProductSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Service.objects.filter(is_active=True).order_by("order", "pk")

    def location(self, item: Service):
        return reverse("catalog:product_detail", args=[item.pk])

    def lastmod(self, item: Service):
        return item.updated_at
