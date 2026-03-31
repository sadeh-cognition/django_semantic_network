from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("django_lightrag", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ConceptSchemeRecord",
        ),
    ]
