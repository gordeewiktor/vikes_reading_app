from django.shortcuts import get_object_or_404

from vikes_reading_app.models import Story, PreReadingExercise, PostReadingQuestion, CustomUser
from .story_repository import StoryRepository

class ORMStoryRepository(StoryRepository):
    """
    Concrete implementation of StoryRepository using Django ORM.
    """

    def delete_story_with_related(self, story_id: int) -> None:
        """
        Deletes story and all its related exercises/questions.
        """
        story = Story.objects.get(pk=story_id)
        PreReadingExercise.objects.filter(story=story).delete()
        PostReadingQuestion.objects.filter(story=story).delete()
        story.delete()

    def create_story(self, author_id: int, data: dict) -> Story:
        """
        Creates a new story with given author and data.
        """
        author = CustomUser.objects.get(id=author_id)
        story = Story.objects.create(author=author, **data)
        return story

    def edit_story(self, story_id: int, data: dict) -> Story:
        story = Story.objects.get(id=story_id)
        for key, value in data.items():
            setattr(story, key, value)
        story.save()
        return story

    def list_home_stories(self, user) -> list:
        if not user.is_authenticated or user.role == 'student':
            return Story.objects.filter(status='published')
        if user.role == 'teacher':
            return Story.objects.all()
        return Story.objects.none()

    def list_author_stories(self, user) -> list:
        return Story.objects.filter(author=user)

    def get_story_by_id(self, story_id: int):
        return get_object_or_404(Story, id=story_id)

    def list_pre_reading_exercises(self, story) -> list:
        return list(PreReadingExercise.objects.filter(story=story).order_by('id'))

    def count_pre_reading_exercises(self, story) -> int:
        return PreReadingExercise.objects.filter(story=story).count()

    def get_pre_reading_exercise(self, exercise_id: int):
        return get_object_or_404(PreReadingExercise, id=exercise_id)

    def create_pre_reading_exercise(self, story, data: dict):
        return PreReadingExercise.objects.create(story=story, **data)

    def update_pre_reading_exercise(self, exercise, data: dict):
        for key, value in data.items():
            setattr(exercise, key, value)
        exercise.save()
        return exercise

    def delete_pre_reading_exercise(self, exercise) -> None:
        exercise.delete()

    def list_post_reading_questions(self, story) -> list:
        return list(PostReadingQuestion.objects.filter(story=story).order_by('id'))

    def count_post_reading_questions(self, story) -> int:
        return PostReadingQuestion.objects.filter(story=story).count()

    def get_post_reading_question(self, question_id: int, story=None):
        if story is None:
            return get_object_or_404(PostReadingQuestion, id=question_id)
        return get_object_or_404(PostReadingQuestion, id=question_id, story=story)

    def create_post_reading_question(self, story, data: dict):
        return PostReadingQuestion.objects.create(story=story, **data)

    def update_post_reading_question(self, question, data: dict):
        for key, value in data.items():
            setattr(question, key, value)
        question.save()
        return question

    def delete_post_reading_question(self, question) -> None:
        question.delete()
