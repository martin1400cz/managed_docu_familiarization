# Generated by Django 4.1.9 on 2024-11-04 17:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mdf", "0003_alter_document_groups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="doc_url",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
