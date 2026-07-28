from __future__ import annotations

import re

from django import forms

from .models import Application, Service
from .utils import clean_phone_number, format_phone_display

LINK_RE = re.compile(r"(https?://|www\.|t\.me/)", re.IGNORECASE)
NAME_MAX_LENGTH = 80
COMMENT_MAX_LENGTH = 1000


class ApplicationForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        label="Что хотите заказать?",
        queryset=Service.objects.none(),
        empty_label="Что хотите заказать?",
        required=True,
    )
    comment = forms.CharField(
        label="Расскажите вашу идею",
        required=False,
        max_length=COMMENT_MAX_LENGTH,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "maxlength": str(COMMENT_MAX_LENGTH),
                "placeholder": "Расскажите вашу идею",
            }
        ),
    )
    consent = forms.BooleanField(
        label="Согласен на обработку персональных данных",
        required=True,
        error_messages={"required": "Подтвердите согласие на обработку персональных данных."},
    )
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(
            attrs={
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
    )

    class Meta:
        model = Application
        fields = ("name", "phone", "email", "service", "comment")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "autocomplete": "name",
                    "maxlength": str(NAME_MAX_LENGTH),
                    "minlength": "2",
                    "placeholder": "Ваше имя",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "autocomplete": "tel",
                    "inputmode": "tel",
                    "placeholder": "Телефон",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "placeholder": "Email",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        services = Service.objects.filter(is_active=True)
        self.fields["service"].queryset = services.order_by("category_parent", "category", "order", "pk")
        self.fields["service"].label_from_instance = lambda service: service.title

    def clean_name(self) -> str:
        name = " ".join((self.cleaned_data.get("name") or "").split())
        letters_count = sum(char.isalpha() for char in name)
        digits_count = sum(char.isdigit() for char in name)

        if len(name) < 2:
            raise forms.ValidationError("Укажите имя не короче 2 символов.")
        if len(name) > NAME_MAX_LENGTH:
            raise forms.ValidationError(f"Имя должно быть не длиннее {NAME_MAX_LENGTH} символов.")
        if letters_count < 2:
            raise forms.ValidationError("Укажите реальное имя.")
        if digits_count > 3 or LINK_RE.search(name):
            raise forms.ValidationError("Имя заполнено некорректно.")

        return name

    def clean_phone(self) -> str:
        phone = clean_phone_number(self.cleaned_data["phone"])
        if not phone:
            raise forms.ValidationError("Укажите телефон в формате +7XXXXXXXXXX.")
        return format_phone_display(phone)

    def clean_comment(self) -> str:
        comment = (self.cleaned_data.get("comment") or "").strip()
        if LINK_RE.search(comment):
            raise forms.ValidationError("Ссылки в комментарии запрещены.")
        return comment

    def clean_website(self) -> str:
        value = (self.cleaned_data.get("website") or "").strip()
        if value:
            raise forms.ValidationError("Не удалось отправить заявку.")
        return value

    def save(self, commit: bool = True) -> Application:
        application = super().save(commit=False)
        application.consent = self.cleaned_data.get("consent", False)
        if commit:
            application.save()
            self.save_m2m()
        return application
