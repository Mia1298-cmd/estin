# Generated by Django 5.2 on 2025-04-23 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='duration',
            field=models.DurationField(help_text='Durée (heures et minutes)'),
        ),
    ]
