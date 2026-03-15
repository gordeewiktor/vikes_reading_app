from vikes_reading_app.models import PostReadingQuestion, PreReadingExercise


class ReadingFlowService:
    STAGE_TRANSITIONS = {
        'pre_reading_time': 'reading',
        'reading_time': 'reading',
        'post_reading_time': 'completed',
    }

    @staticmethod
    def get_resume_target(progress, session_progress, story):
        if progress.is_empty and not session_progress:
            return 'pre_reading_read'

        post_total = PostReadingQuestion.objects.filter(story=story).count()
        answers = progress.answers_given if progress and progress.answers_given else {}
        if post_total > 0 and len(answers) == post_total:
            return 'post_reading_summary'

        return None

    @staticmethod
    def get_pre_reading_score(request, story):
        exercises = PreReadingExercise.objects.filter(story=story)
        total = exercises.count()
        correct = 0

        for exercise in exercises:
            selected = request.session.get(f'answer_{exercise.id}')
            if selected:
                correct_answer = exercise.option_1 if exercise.is_option_1_correct else exercise.option_2
                if selected == correct_answer:
                    correct += 1

        return correct, total

    @staticmethod
    def get_post_reading_score(progress):
        if not progress or not progress.answers_given:
            return 0, 0
        total = len(progress.answers_given)
        correct = sum(1 for value in progress.answers_given.values() if value)
        return correct, total

    @classmethod
    def get_next_stage(cls, time_field):
        return cls.STAGE_TRANSITIONS[time_field]
