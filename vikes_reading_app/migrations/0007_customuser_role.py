# Generated by Django 5.1.4 on 2024-12-30 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vikes_reading_app', '0006_remove_progress_vikes_readi_student_f59a45_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('teacher', 'Teacher'), ('student', 'Student')], default='student', max_length=10),
        ),
    ]
