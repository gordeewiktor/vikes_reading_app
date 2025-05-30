# Generated by Django 5.1.4 on 2024-12-29 06:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vikes_reading_app', '0004_remove_customuser_english_level_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreReadingExercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('words', 'Listening to the difference in words'), ('sentences', 'Listening to the differnce in sentence')], max_length=20)),
                ('question_text', models.CharField(max_length=500)),
                ('option_1', models.CharField(max_length=100)),
                ('option_2', models.CharField(max_length=100)),
                ('correct_answer', models.CharField(max_length=100)),
                ('audio_file', models.FileField(blank=True, null=True, upload_to='pre_reading_audio/')),
                ('order', models.PositiveIntegerField(default=0)),
                ('story', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pre_reading_exercises', to='vikes_reading_app.story')),
            ],
        ),
    ]
