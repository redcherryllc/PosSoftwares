# Generated by Django 4.2.10 on 2025-05-06 05:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0031_alter_products_update_tm'),
    ]

    operations = [
        migrations.AlterField(
            model_name='products',
            name='category',
            field=models.ForeignKey(blank=True, db_column='category_fk_id', limit_choices_to={'category_type': 'PRODUCT_TYPE'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='pos.category'),
        ),
    ]
