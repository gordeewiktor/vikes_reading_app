from abc import ABC, abstractmethod
from vikes_reading_app.dtos.progress_session import SessionProgressDTO

class ProgressRepository(ABC):

    @abstractmethod
    def get_progress(self, student_id: int, story_id: int) -> SessionProgressDTO:
       
        pass

    @abstractmethod
    def get_progress_model(self, student, story):
        pass

    @abstractmethod
    def get_or_create_progress(self, student, story):
        pass

    @abstractmethod
    def save_progress(self, progress):
        pass

    @abstractmethod
    def save_time(self, student, story, time_field: str, current_stage: str, time_spent: int):
        pass

    @abstractmethod
    def delete_progress(self, student, story) -> None:
        pass

    @abstractmethod
    def list_story_titles_for_student(self, student) -> list:
        pass

    @abstractmethod
    def list_progress_records(self, student, stories) -> list:
        pass
