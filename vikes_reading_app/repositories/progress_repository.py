from abc import ABC, abstractmethod
from vikes_reading_app.dtos.progress_session import SessionProgressDTO

class ProgressRepository(ABC):

    @abstractmethod
    def get_progress(self, student_id: int, story_id: int) -> SessionProgressDTO:
       
        pass