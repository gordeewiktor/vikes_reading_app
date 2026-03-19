from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vikes_reading_app', '0015_alter_progress_score'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='progress',
            constraint=models.UniqueConstraint(
                fields=('student', 'read_story'),
                name='unique_progress_per_student_story',
            ),
        ),
    ]
