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

    def get_progress_model(self, student, story):
        return Progress.objects.filter(student=student, read_story=story).first()

    def get_or_create_progress(self, student, story):
        return Progress.objects.get_or_create(student=student, read_story=story)

    def save_progress(self, progress):
        progress.save()
        return progress

    def save_time(self, student, story, time_field: str, current_stage: str, time_spent: int):
        progress, _ = Progress.objects.update_or_create(
            student=student,
            read_story=story,
            defaults={
                time_field: time_spent,
                'current_stage': current_stage,
            }
        )
        return progress

    def delete_progress(self, student, story) -> None:
        Progress.objects.filter(student=student, read_story=story).delete()

    def list_story_titles_for_student(self, student) -> list:
        return list(
            Progress.objects
            .filter(student=student)
            .select_related('read_story')
            .values_list('read_story__title', flat=True)
            .distinct()
        )

    def list_progress_records(self, student, stories) -> list:
        return Progress.objects.filter(
            student=student,
            read_story__in=stories
        ).select_related('read_story').prefetch_related(
            'read_story__pre_reading_exercises',
            'read_story__post_reading_questions',
        )
