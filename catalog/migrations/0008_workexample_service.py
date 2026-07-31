from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_merge_homepage_into_sitesettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="workexample",
            name="service",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="work_examples",
                to="catalog.service",
                verbose_name="Товар для перехода",
            ),
        ),
    ]
