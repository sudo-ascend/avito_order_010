from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_workexample_service"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="contact_success_message",
            field=models.CharField(
                default="Создаем моменты счастья",
                max_length=255,
                verbose_name="Сообщение об успешной отправке",
            ),
        ),
    ]
