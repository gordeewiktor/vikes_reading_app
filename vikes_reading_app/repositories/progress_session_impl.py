from .progress_repository import ProgressRepository
from vikes_reading_app.dtos.progress_session import SessionProgressDTO

class SessionProgressRepository(ProgressRepository):
    def __init__(self, session: dict):
        self.session = session

    def get_progress(self, student_id: int, story_id: int) -> SessionProgressDTO:
        session_key = f"pre_reading_progress_{story_id}"
        data = self.session.get(session_key)

        if not data:
            return None

        return SessionProgressDTO(
            story_id=story_id,
            score=data.get("score", 0.0),
            answers_given=data.get("answers_given", {}),
            current_stage=data.get("current_stage", "pre_reading"),
            pre_reading_time=data.get("pre_reading_time", 0),
            post_reading_time=data.get("post_reading_time", 0),
        )