# Generated by Django 4.2.10 on 2025-04-27 16:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0024_alter_inventoryheader_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='inventoryheader',
            options={'managed': False},
        ),
    ]
