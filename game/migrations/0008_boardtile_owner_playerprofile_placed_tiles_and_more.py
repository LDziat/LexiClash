# Generated by Django 5.1.2 on 2024-11-03 17:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0007_tile_owner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='boardtile',
            name='owner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='playerprofile',
            name='placed_tiles',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='playerprofile',
            name='placed_tiles_history',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
