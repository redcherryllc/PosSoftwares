# Generated by Django 4.2.10 on 2025-04-28 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0027_remove_inventoryheader_product_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryheader',
            name='grnno',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
    ]
