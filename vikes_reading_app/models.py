# --- Imports ---

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


# --- Role Choices ---

ROLE_CHOICES = [
    ('teacher', 'Teacher'),
    ('student', 'Student'),
]


# --- Models ---

# Custom User Model with roles to distinguish between teachers and students
class CustomUser(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',  # Default role is "Student"
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# Model representing a story that can be read by students
class Story(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=200)  # Title of the story
    description = models.TextField()  # Brief description of the story
    content = models.TextField()  # Full content of the story
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Author of the story
    narration_audio = models.FileField(upload_to='story_audio/', blank=True, null=True)  # Optional narration audio file
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
    )

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=['author']),
        ]


# Model tracking the progress of a student reading a story
class Progress(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Student reading the story
    read_story = models.ForeignKey(Story, on_delete=models.CASCADE)  # Story being read
    score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )  # Score achieved by the student
    answers_given = models.JSONField(default=dict)  # Answers provided by the student in exercises
    current_stage = models.CharField(
        max_length=20,
        choices=[
            ('pre_reading', 'Pre-Reading'),
            ('reading', 'Reading'),
            ('post_reading', 'Post-Reading'),
            ('completed', 'Completed'),
        ],
        default='pre_reading',
    )  # Current stage of reading
    reading_time = models.IntegerField(default=0, help_text="Time in seconds")  # Time spent reading
    pre_reading_time = models.IntegerField(default=0, help_text="Time in seconds")  # Time spent in pre-reading exercises
    post_reading_time = models.IntegerField(default=0, help_text="Time in seconds")  # Time spent in post-reading questions
    post_reading_lookups = models.JSONField(default=dict)  # Additional data/lookups for post-reading phase

    def __str__(self):
        return f"{self.student.username} - {self.read_story.title} - {self.current_stage}"

    def _normalized_answers(self):
        answers = self.answers_given or {}
        if 'pre_reading' in answers or 'post_reading' in answers:
            return {
                'pre_reading': answers.get('pre_reading', {}),
                'post_reading': answers.get('post_reading', {}),
            }
        return {
            'pre_reading': {},
            'post_reading': answers,
        }

    @staticmethod
    def _percentage(correct, total):
        if total == 0:
            return None
        return round((correct / total) * 100)

    def get_pre_reading_stats(self):
        answers = self._normalized_answers()['pre_reading']
        exercises = self.read_story.pre_reading_exercises.all()
        total = exercises.count()
        correct = 0

        for exercise in exercises:
            selected = answers.get(str(exercise.id))
            correct_answer = exercise.option_1 if exercise.is_option_1_correct else exercise.option_2
            if selected == correct_answer:
                correct += 1

        return {
            'correct': correct,
            'total': total,
            'percentage': self._percentage(correct, total),
            'time_spent': self.pre_reading_time,
        }

    def get_post_reading_stats(self):
        answers = self._normalized_answers()['post_reading']
        questions = self.read_story.post_reading_questions.all()
        total = questions.count()
        correct = 0

        for question in questions:
            answer_data = answers.get(str(question.id))
            if isinstance(answer_data, dict):
                is_correct = answer_data.get('is_correct', False)
            else:
                is_correct = bool(answer_data)
            if is_correct:
                correct += 1

        return {
            'correct': correct,
            'total': total,
            'percentage': self._percentage(correct, total),
            'time_spent': self.post_reading_time,
        }

    def get_overall_stats(self):
        pre_stats = self.get_pre_reading_stats()
        post_stats = self.get_post_reading_stats()
        correct = pre_stats['correct'] + post_stats['correct']
        total = pre_stats['total'] + post_stats['total']

        return {
            'correct': correct,
            'total': total,
            'percentage': self._percentage(correct, total),
        }

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'read_story'],
                name='unique_progress_per_student_story',
            ),
        ]


# Model holding pre-reading exercises linked to a story
class PreReadingExercise(models.Model):
    story = models.ForeignKey('Story', on_delete=models.CASCADE, related_name='pre_reading_exercises')  # Associated story
    question_text = models.CharField(max_length=500)  # Text of the pre-reading question
    option_1 = models.CharField(max_length=100)  # First answer option
    option_2 = models.CharField(max_length=100)  # Second answer option
    is_option_1_correct = models.BooleanField(default=False)  # Whether option 1 is correct
    is_option_2_correct = models.BooleanField(default=False)  # Whether option 2 is correct
    audio_file = models.FileField(upload_to='pre_reading_audio/', blank=True, null=True)  # Optional audio for the question

    def __str__(self):
        return f"{self.story.title} - {self.question_text}"


# Model holding post-reading questions linked to a story
class PostReadingQuestion(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='post_reading_questions')  # Associated story
    question_text = models.CharField(max_length=500)  # Text of the post-reading question
    option_1 = models.CharField(max_length=100)  # Option 1
    option_2 = models.CharField(max_length=100)  # Option 2
    option_3 = models.CharField(max_length=100)  # Option 3
    option_4 = models.CharField(max_length=100)  # Option 4
    correct_option = models.PositiveSmallIntegerField(
        choices=[
            (1, "Option 1"),
            (2, "Option 2"),
            (3, "Option 3"),
            (4, "Option 4")
        ]
    )  # Correct option number
    explanation = models.TextField(blank=True)  # Explanation for the correct answer

    def __str__(self):
        return f"{self.story.title} - {self.question_text}"
