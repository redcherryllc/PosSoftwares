# Generated by Django 4.2.10 on 2025-06-18 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0034_alter_salesheader_update_marks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesheader',
            name='update_marks',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
