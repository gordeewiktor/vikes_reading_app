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