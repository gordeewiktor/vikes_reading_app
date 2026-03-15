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

    @abstractmethod
    def list_home_stories(self, user) -> list:
        pass

    @abstractmethod
    def list_author_stories(self, user) -> list:
        pass

    @abstractmethod
    def get_story_by_id(self, story_id: int):
        pass

    @abstractmethod
    def list_pre_reading_exercises(self, story) -> list:
        pass

    @abstractmethod
    def count_pre_reading_exercises(self, story) -> int:
        pass

    @abstractmethod
    def get_pre_reading_exercise(self, exercise_id: int):
        pass

    @abstractmethod
    def create_pre_reading_exercise(self, story, data: dict):
        pass

    @abstractmethod
    def update_pre_reading_exercise(self, exercise, data: dict):
        pass

    @abstractmethod
    def delete_pre_reading_exercise(self, exercise) -> None:
        pass

    @abstractmethod
    def list_post_reading_questions(self, story) -> list:
        pass

    @abstractmethod
    def count_post_reading_questions(self, story) -> int:
        pass

    @abstractmethod
    def get_post_reading_question(self, question_id: int, story=None):
        pass

    @abstractmethod
    def create_post_reading_question(self, story, data: dict):
        pass

    @abstractmethod
    def update_post_reading_question(self, question, data: dict):
        pass

    @abstractmethod
    def delete_post_reading_question(self, question) -> None:
        pass
