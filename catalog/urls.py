from django.urls import path

from .api import application_create_api
from .views import index, robots_txt

app_name = "catalog"

urlpatterns = [
    path("", index, name="index"),
    path("api/application/", application_create_api, name="application_create_api"),
    path("robots.txt", robots_txt, name="robots_txt"),
]
