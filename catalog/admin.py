from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.files.storage import FileSystemStorage
from django.http import HttpRequest
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import Application, Review, Service, SiteSettings, Step, TelegramSubscriber, WorkExample

admin.site.site_header = settings.SITE_NAME
admin.site.site_title = settings.SITE_NAME
admin.site.index_title = "Управление сайтом"

IMAGE_UPLOAD_WIDGET = forms.ClearableFileInput(attrs={"accept": "image/*"})
IMAGE_UPLOAD_STORAGE = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleImageInput(attrs={"accept": "image/*"})

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return [single_file_clean(data, initial)]


def build_asset_url(path: str) -> str:
    if not path:
        return ""
    if path.startswith(("http://", "https://", "/")):
        return path
    return static(path)


def save_admin_upload(upload, upload_to: str) -> str:
    extension = Path(upload.name).suffix.lower()
    filename = f"{upload_to.rstrip('/')}/{uuid4().hex}{extension}"
    saved_name = IMAGE_UPLOAD_STORAGE.save(filename, upload)
    return f"{settings.MEDIA_URL}{saved_name}".replace("\\", "/")


class AdminStyleMixin:
    class Media:
        css = {"all": ("catalog/admin.css",)}


class AdminImageUploadFormMixin(forms.ModelForm):
    image_upload_map: dict[str, dict[str, str]] = {}
    multi_image_upload_map: dict[str, dict[str, str]] = {}

    def save(self, commit=True):
        instance = super().save(commit=False)
        for upload_field, config in self.image_upload_map.items():
            upload = self.cleaned_data.get(upload_field)
            if upload:
                setattr(instance, config["target_field"], save_admin_upload(upload, config["upload_to"]))
        for upload_field, config in self.multi_image_upload_map.items():
            uploads = self.cleaned_data.get(upload_field) or []
            if uploads:
                setattr(
                    instance,
                    config["target_field"],
                    [save_admin_upload(upload, config["upload_to"]) for upload in uploads],
                )
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class SiteSettingsAdminForm(AdminImageUploadFormMixin):
    logo_upload = forms.FileField(label="Логотип", required=False, widget=IMAGE_UPLOAD_WIDGET)
    favicon_upload = forms.FileField(label="Favicon", required=False, widget=IMAGE_UPLOAD_WIDGET)
    share_image_upload = forms.FileField(label="Изображение превью ссылки", required=False, widget=IMAGE_UPLOAD_WIDGET)
    hero_image_upload = forms.FileField(label="Hero-изображение", required=False, widget=IMAGE_UPLOAD_WIDGET)
    about_image_1_upload = forms.FileField(label="Первая картинка", required=False, widget=IMAGE_UPLOAD_WIDGET)
    about_image_2_upload = forms.FileField(label="Вторая картинка", required=False, widget=IMAGE_UPLOAD_WIDGET)
    about_image_3_upload = forms.FileField(label="Третья картинка", required=False, widget=IMAGE_UPLOAD_WIDGET)
    contact_image_upload = forms.FileField(label="Картинка блока контактов", required=False, widget=IMAGE_UPLOAD_WIDGET)

    image_upload_map = {
        "logo_upload": {"target_field": "logo_path", "upload_to": "admin/site"},
        "favicon_upload": {"target_field": "favicon_path", "upload_to": "admin/site"},
        "share_image_upload": {"target_field": "share_image_path", "upload_to": "admin/share"},
        "hero_image_upload": {"target_field": "hero_image_path", "upload_to": "admin/home"},
        "about_image_1_upload": {"target_field": "about_image_1_path", "upload_to": "admin/home"},
        "about_image_2_upload": {"target_field": "about_image_2_path", "upload_to": "admin/home"},
        "about_image_3_upload": {"target_field": "about_image_3_path", "upload_to": "admin/home"},
        "contact_image_upload": {"target_field": "contact_image_path", "upload_to": "admin/home"},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telegram_url"].help_text = "Укажите полную ссылку, например https://t.me/your_name"
        self.fields["whatsapp_url"].help_text = "Укажите полную ссылку, например https://wa.me/79991234567"
        self.fields["max_url"].help_text = "Укажите полную ссылку"
        self.fields["instagram_url"].help_text = "Укажите полную ссылку"

    class Meta:
        model = SiteSettings
        exclude = (
            "logo_path",
            "favicon_path",
            "share_image_path",
            "hero_image_path",
            "about_image_1_path",
            "about_image_2_path",
            "about_image_3_path",
            "contact_image_path",
            "seo_title",
            "seo_description",
        )


class ServiceAdminForm(AdminImageUploadFormMixin):
    image_upload = forms.FileField(label="Основное изображение", required=False, widget=IMAGE_UPLOAD_WIDGET)
    extra_image_uploads = MultipleImageField(
        label="Дополнительные изображения",
        required=False,
        help_text="Можно выбрать несколько файлов. Новая загрузка заменит текущий список.",
    )

    image_upload_map = {
        "image_upload": {"target_field": "image_path", "upload_to": "admin/services"},
    }
    multi_image_upload_map = {
        "extra_image_uploads": {"target_field": "extra_image_paths", "upload_to": "admin/services"},
    }

    class Meta:
        model = Service
        exclude = ("image_path", "extra_image_paths")


class WorkExampleAdminForm(AdminImageUploadFormMixin):
    image_upload = forms.FileField(label="Изображение", required=False, widget=IMAGE_UPLOAD_WIDGET)

    image_upload_map = {
        "image_upload": {"target_field": "image_path", "upload_to": "admin/works"},
    }

    class Meta:
        model = WorkExample
        exclude = ("image_path",)


class StepAdminForm(AdminImageUploadFormMixin):
    icon_upload = forms.FileField(label="Иконка", required=False, widget=IMAGE_UPLOAD_WIDGET)

    image_upload_map = {
        "icon_upload": {"target_field": "icon_path", "upload_to": "admin/steps"},
    }

    class Meta:
        model = Step
        exclude = ("icon_path",)


class SingletonAdmin(AdminStyleMixin, admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return not self.model.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def changelist_view(self, request: HttpRequest, extra_context=None):
        obj = self.model.objects.first()
        if obj:
            return redirect(reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change", args=[obj.pk]))
        return redirect(reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_add"))


class ImagePreviewAdminMixin:
    @staticmethod
    def render_image_preview(path: str, alt: str = ""):
        if not path:
            return format_html('<div class="admin-image-preview admin-image-preview--empty">Изображение не загружено</div>')
        url = build_asset_url(path)
        return format_html(
            '<a class="admin-image-preview" href="{}" target="_blank" rel="noopener noreferrer">'
            '<img src="{}" alt="{}"></a>',
            url,
            url,
            alt or "Превью",
        )

    @staticmethod
    def render_image_preview_gallery(paths: list[str] | tuple[str, ...] | None, alt_prefix: str):
        items = [path for path in (paths or []) if path]
        if not items:
            return format_html('<div class="admin-image-preview admin-image-preview--empty">Изображения не загружены</div>')
        return format_html(
            '<div class="admin-image-preview-grid">{}</div>',
            format_html_join(
                "",
                '<a class="admin-image-preview" href="{}" target="_blank" rel="noopener noreferrer">'
                '<img src="{}" alt="{}"></a>',
                (
                    (url, url, f"{alt_prefix} {index}")
                    for index, path in enumerate(items, start=1)
                    for url in [build_asset_url(path)]
                ),
            ),
        )


@admin.register(SiteSettings)
class SiteSettingsAdmin(ImagePreviewAdminMixin, SingletonAdmin):
    form = SiteSettingsAdminForm
    readonly_fields = (
        "updated_at",
        "logo_preview",
        "favicon_preview",
        "share_image_preview",
        "hero_image_preview",
        "about_image_1_preview",
        "about_image_2_preview",
        "about_image_3_preview",
        "contact_image_preview",
    )
    fieldsets = (
        ("Бренд", {"fields": ("site_name", "brand_tagline", "logo_upload", "logo_preview", "favicon_upload", "favicon_preview")}),
        (
            "Превью ссылки",
            {
                "fields": (
                    "share_title",
                    "share_description",
                    "share_image_upload",
                    "share_image_preview",
                    "share_image_alt",
                )
            },
        ),
        (
            "Hero",
            {
                "fields": (
                    "hero_title",
                    "hero_text",
                    "hero_primary_text",
                    "hero_primary_link",
                    "hero_secondary_text",
                    "hero_secondary_link",
                    "hero_image_upload",
                    "hero_image_preview",
                    "hero_image_alt",
                    "hero_advantages_text",
                )
            },
        ),
        (
            "О нас",
            {
                "fields": (
                    "about_title",
                    "about_lead",
                    "about_text",
                    "about_list",
                    "about_image_1_upload",
                    "about_image_1_preview",
                    "about_image_1_alt",
                    "about_image_2_upload",
                    "about_image_2_preview",
                    "about_image_2_alt",
                    "about_image_3_upload",
                    "about_image_3_preview",
                    "about_image_3_alt",
                )
            },
        ),
        (
            "Каталог и витрина",
            {
                "fields": (
                    "catalog_title",
                    "works_title",
                    "works_button_text",
                    "works_button_link",
                    "reviews_title",
                    "process_title",
                )
            },
        ),
        (
            "Контакты и форма",
            {
                "fields": (
                    "phone",
                    "email",
                    "application_email",
                    "telegram_url",
                    "whatsapp_url",
                    "max_url",
                    "instagram_url",
                    "address",
                    "work_time",
                    "contact_title",
                    "contact_text",
                    "contact_image_upload",
                    "contact_image_preview",
                    "contact_image_alt",
                    "contact_success_message",
                )
            },
        ),
        ("Контент футера", {"fields": ("footer_description", "footer_promo", "footer_navigation_title", "footer_contacts_title", "policy_text")}),
        ("Интеграции", {"fields": ("metrika_code",)}),
        ("Служебное", {"fields": ("updated_at",)}),
    )

    @admin.display(description="Превью логотипа")
    def logo_preview(self, obj: SiteSettings):
        return self.render_image_preview(getattr(obj, "logo_path", ""), obj.site_name)

    @admin.display(description="Превью favicon")
    def favicon_preview(self, obj: SiteSettings):
        return self.render_image_preview(getattr(obj, "favicon_path", ""), "Favicon")

    @admin.display(description="Превью ссылки")
    def share_image_preview(self, obj: SiteSettings):
        return self.render_image_preview(getattr(obj, "share_image_path", ""), obj.share_image_alt or obj.site_name)

    @admin.display(description="Превью hero")
    def hero_image_preview(self, obj: SiteSettings):
        return self.render_image_preview(getattr(obj, "hero_image_path", ""), obj.hero_image_alt)

    @admin.display(description="Превью первой картинки")
    def about_image_1_preview(self, obj: SiteSettings):
        return self.render_image_preview(getattr(obj, "about_image_1_path", ""), obj.about_image_1_alt)

    @admin.display(description="Превью второй картинки")
    def about_image_2_preview(self, obj: SiteSettings):
        return self.render_image_preview(getattr(obj, "about_image_2_path", ""), obj.about_image_2_alt)

    @admin.display(description="Превью третьей картинки")
    def about_image_3_preview(self, obj: SiteSettings):
        return self.render_image_preview(getattr(obj, "about_image_3_path", ""), obj.about_image_3_alt)

    @admin.display(description="Превью контактов")
    def contact_image_preview(self, obj: SiteSettings):
        return self.render_image_preview(getattr(obj, "contact_image_path", ""), obj.contact_image_alt)


@admin.register(Service)
class ServiceAdmin(ImagePreviewAdminMixin, AdminStyleMixin, admin.ModelAdmin):
    form = ServiceAdminForm
    list_display = ("title", "category", "category_parent", "order", "is_active")
    list_filter = ("is_active", "category", "category_parent")
    search_fields = ("title", "description", "category", "category_parent", "supplier_name")
    readonly_fields = ("image_preview", "extra_images_preview")
    fieldsets = (
        ("Основное", {"fields": ("title", "description", "order", "is_active")}),
        ("Каталог", {"fields": ("nm_id", "supplier_name", "category", "category_parent", "card_url")}),
        ("Изображения", {"fields": ("image_upload", "image_preview", "extra_image_uploads", "extra_images_preview")}),
    )

    @admin.display(description="Превью изображения")
    def image_preview(self, obj: Service):
        return self.render_image_preview(getattr(obj, "image_path", ""), obj.title)

    @admin.display(description="Превью дополнительных изображений")
    def extra_images_preview(self, obj: Service):
        return self.render_image_preview_gallery(getattr(obj, "extra_image_paths", []), obj.title or "Изображение")


@admin.register(WorkExample)
class WorkExampleAdmin(ImagePreviewAdminMixin, AdminStyleMixin, admin.ModelAdmin):
    form = WorkExampleAdminForm
    list_display = ("title", "show_on_home", "order")
    list_filter = ("show_on_home",)
    search_fields = ("title", "description", "alt")
    readonly_fields = ("image_preview",)
    fieldsets = (
        ("Основное", {"fields": ("title", "description", "order", "show_on_home")}),
        ("Изображение", {"fields": ("image_upload", "image_preview", "alt")}),
    )

    @admin.display(description="Превью изображения")
    def image_preview(self, obj: WorkExample):
        return self.render_image_preview(getattr(obj, "image_path", ""), obj.alt or obj.title)


@admin.register(Step)
class StepAdmin(ImagePreviewAdminMixin, AdminStyleMixin, admin.ModelAdmin):
    form = StepAdminForm
    list_display = ("title", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    readonly_fields = ("icon_preview",)
    fieldsets = (
        ("Основное", {"fields": ("title", "description", "order", "is_active")}),
        ("Иконка", {"fields": ("icon_upload", "icon_preview")}),
    )

    @admin.display(description="Превью иконки")
    def icon_preview(self, obj: Step):
        return self.render_image_preview(getattr(obj, "icon_path", ""), obj.title)


@admin.register(Review)
class ReviewAdmin(AdminStyleMixin, admin.ModelAdmin):
    list_display = ("rating", "order", "is_active", "short_text")
    list_filter = ("rating", "is_active")
    search_fields = ("text",)

    @admin.display(description="Текст")
    def short_text(self, obj: Review):
        return obj.text[:80]


@admin.register(Application)
class ApplicationAdmin(AdminStyleMixin, admin.ModelAdmin):
    list_display = ("name", "phone", "email", "service", "status", "created_at")
    list_filter = ("status", "service", "created_at")
    search_fields = ("name", "phone", "email", "service__title", "comment")
    readonly_fields = ("created_at", "ip_address", "user_agent")


@admin.register(TelegramSubscriber)
class TelegramSubscriberAdmin(AdminStyleMixin, admin.ModelAdmin):
    list_display = ("chat_id", "username", "first_name", "last_name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("chat_id", "username", "first_name", "last_name")
    readonly_fields = ("subscribed_at", "updated_at")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
