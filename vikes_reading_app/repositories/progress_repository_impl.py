from .progress_repository import ProgressRepository
from vikes_reading_app.models import Progress
from vikes_reading_app.dtos.progress_session import SessionProgressDTO

class ORMProgressRepository(ProgressRepository):
    def get_progress(self, student_id: int, story_id: int) -> SessionProgressDTO:

        progress_model = Progress.objects.filter(student_id=student_id, read_story_id=story_id).first()

        if not progress_model:
            return SessionProgressDTO(
                story_id=story_id,
                score=0.0,
                answers_given={},
                current_stage="pre_reading",
                pre_reading_time=0,
                post_reading_time=0,
                )
        
        return SessionProgressDTO(
            story_id=progress_model.read_story_id,
            score=progress_model.score,
            answers_given=progress_model.answers_given,
            current_stage=progress_model.current_stage,
            pre_reading_time=progress_model.pre_reading_time,
            post_reading_time=progress_model.post_reading_time,
        )