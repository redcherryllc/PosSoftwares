# Generated by Django 4.2.10 on 2025-05-06 05:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0029_alter_purchaseorders_pono'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='category',
            field=models.ForeignKey(blank=True, db_column='category_fk_id', limit_choices_to={'category_type': 'product_type'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='pos.category'),
        ),
        migrations.AlterField(
            model_name='products',
            name='update_tm',
            field=models.DateTimeField(default='1900-01-01'),
        ),
    ]
