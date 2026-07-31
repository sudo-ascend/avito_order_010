from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from catalog.sitemaps import HomeSitemap, ProductSitemap


sitemaps = {
    "home": HomeSitemap,
    "products": ProductSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("", include(("catalog.urls", "catalog"), namespace="catalog")),
]

handler400 = "catalog.views.bad_request"
handler403 = "catalog.views.permission_denied"
handler404 = "catalog.views.page_not_found"
handler500 = "catalog.views.server_error"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
