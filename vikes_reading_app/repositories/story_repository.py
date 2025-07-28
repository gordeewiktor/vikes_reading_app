from abc import ABC, abstractmethod

class StoryRepository(ABC):
    """
    Interface (contract) for Story data operations.
    """

    @abstractmethod
    def delete_story_with_related(self, story_id: int) -> None:
        """
        Delete the story and all related PreReadingExercises and PostReadingQuestions.
        """
        pass

    @abstractmethod
    def create_story(self, author_id: int, data: dict) -> object:
        """
        Create a new story with the given data and author.
        """
        pass

    @abstractmethod
    def edit_story(self, story_id: int, data: dict) -> object:
        """
        Edit an existing story with new data.
        """
        pass