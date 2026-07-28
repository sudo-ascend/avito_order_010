from django.db import migrations, models
import django.db.models.deletion


def clear_page_data(apps, schema_editor):
    Application = apps.get_model("catalog", "Application")
    Equipment = apps.get_model("catalog", "Equipment")
    Page = apps.get_model("catalog", "Page")
    Service = apps.get_model("catalog", "Service")
    Step = apps.get_model("catalog", "Step")
    WorkExample = apps.get_model("catalog", "WorkExample")

    Application.objects.exclude(page=None).update(page=None)
    Service.objects.exclude(page=None).update(page=None)
    WorkExample.objects.exclude(page=None).update(page=None)
    Step.objects.exclude(page=None).update(page=None)
    Equipment.objects.exclude(page=None).update(page=None)
    Page.objects.all().delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="service",
            name="page",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="services",
                to="catalog.page",
            ),
        ),
        migrations.RunPython(clear_page_data, noop_reverse),
    ]
