# Generated by Django 5.1.2 on 2024-11-03 08:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('letter', models.CharField(max_length=1)),
                ('is_blank', models.BooleanField(default=False)),
                ('effects', models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PlayerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_played_time', models.DateTimeField(blank=True, null=True)),
                ('cooldown_remaining', models.IntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BoardTile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x_coordinate', models.IntegerField()),
                ('y_coordinate', models.IntegerField()),
                ('tile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='game.tile')),
            ],
            options={
                'unique_together': {('x_coordinate', 'y_coordinate')},
            },
        ),
    ]
