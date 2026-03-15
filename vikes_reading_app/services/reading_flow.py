from vikes_reading_app.models import PostReadingQuestion, PreReadingExercise


class ReadingFlowService:
    STAGE_TRANSITIONS = {
        'pre_reading_time': 'reading',
        'reading_time': 'reading',
        'post_reading_time': 'completed',
    }

    @staticmethod
    def _normalized_answers(progress):
        if not progress or not progress.answers_given:
            return {'pre_reading': {}, 'post_reading': {}}

        answers = progress.answers_given
        if 'pre_reading' in answers or 'post_reading' in answers:
            return {
                'pre_reading': answers.get('pre_reading', {}),
                'post_reading': answers.get('post_reading', {}),
            }

        # Backward compatibility for older flat post-reading answers.
        return {
            'pre_reading': {},
            'post_reading': answers,
        }

    @classmethod
    def get_pre_reading_answers(cls, progress):
        return cls._normalized_answers(progress)['pre_reading']

    @classmethod
    def get_post_reading_answers(cls, progress):
        return cls._normalized_answers(progress)['post_reading']

    @classmethod
    def set_pre_reading_answer(cls, progress, exercise_id, selected_answer):
        answers = cls._normalized_answers(progress)
        answers['pre_reading'][str(exercise_id)] = selected_answer
        progress.answers_given = answers

    @classmethod
    def set_post_reading_answer(cls, progress, question_id, is_correct):
        answers = cls._normalized_answers(progress)
        answers['post_reading'][str(question_id)] = is_correct
        progress.answers_given = answers

    @classmethod
    def get_resume_target(cls, progress, story):
        if not progress or progress.is_empty:
            return 'pre_reading_read'

        pre_total = PreReadingExercise.objects.filter(story=story).count()
        pre_answers = cls.get_pre_reading_answers(progress)
        if pre_total > 0 and len(pre_answers) < pre_total:
            return 'pre_reading_read'

        post_total = PostReadingQuestion.objects.filter(story=story).count()
        post_answers = cls.get_post_reading_answers(progress)
        if post_total > 0 and len(post_answers) == post_total:
            return 'post_reading_summary'

        return None

    @classmethod
    def get_pre_reading_score(cls, progress, story):
        exercises = PreReadingExercise.objects.filter(story=story)
        answers = cls.get_pre_reading_answers(progress)
        total = exercises.count()
        correct = 0

        for exercise in exercises:
            selected = answers.get(str(exercise.id))
            if selected:
                correct_answer = exercise.option_1 if exercise.is_option_1_correct else exercise.option_2
                if selected == correct_answer:
                    correct += 1

        return correct, total

    @classmethod
    def get_post_reading_score(cls, progress):
        answers = cls.get_post_reading_answers(progress)
        if not answers:
            return 0, 0
        total = len(answers)
        correct = sum(1 for value in answers.values() if value)
        return correct, total

    @classmethod
    def get_next_stage(cls, time_field):
        return cls.STAGE_TRANSITIONS[time_field]
