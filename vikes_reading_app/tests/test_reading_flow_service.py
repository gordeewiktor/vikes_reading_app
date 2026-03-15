import pytest

from vikes_reading_app.dtos.progress_session import SessionProgressDTO
from vikes_reading_app.services.reading_flow import ReadingFlowService


pytestmark = pytest.mark.django_db


# ========================
# 🧭 Resume Target
# ========================

def test_get_resume_target_redirects_to_pre_reading_when_no_progress(published_story):
    target = ReadingFlowService.get_resume_target(None, published_story)

    assert target == 'pre_reading_read'


def test_get_resume_target_redirects_to_pre_reading_when_pre_reading_incomplete(
    published_story, two_pre_reading_exercises
):
    ex1, ex2 = two_pre_reading_exercises
    progress = SessionProgressDTO(
        story_id=published_story.id,
        answers_given={
            'pre_reading': {
                str(ex1.id): ex1.option_1,
            },
            'post_reading': {},
        },
        current_stage='pre_reading',
    )

    target = ReadingFlowService.get_resume_target(progress, published_story)

    assert target == 'pre_reading_read'


def test_get_resume_target_redirects_to_post_reading_summary_when_post_reading_complete(
    published_story, post_reading_question
):
    progress = SessionProgressDTO(
        story_id=published_story.id,
        answers_given={
            'pre_reading': {},
            'post_reading': {
                str(post_reading_question.id): True,
            },
        },
        current_stage='post_reading',
    )

    target = ReadingFlowService.get_resume_target(progress, published_story)

    assert target == 'post_reading_summary'


def test_get_resume_target_returns_none_when_pre_reading_done_and_post_reading_not_finished(
    published_story, two_pre_reading_exercises, post_reading_question
):
    ex1, ex2 = two_pre_reading_exercises
    progress = SessionProgressDTO(
        story_id=published_story.id,
        answers_given={
            'pre_reading': {
                str(ex1.id): ex1.option_1,
                str(ex2.id): ex2.option_2,
            },
            'post_reading': {},
        },
        current_stage='reading',
    )

    target = ReadingFlowService.get_resume_target(progress, published_story)

    assert target is None


# ========================
# 📊 Score Computation
# ========================

def test_get_pre_reading_score_counts_correct_answers(published_story, two_pre_reading_exercises):
    ex1, ex2 = two_pre_reading_exercises
    progress = SessionProgressDTO(
        story_id=published_story.id,
        answers_given={
            'pre_reading': {
                str(ex1.id): ex1.option_1,
                str(ex2.id): ex2.option_1,
            },
            'post_reading': {},
        },
    )

    correct, total = ReadingFlowService.get_pre_reading_score(progress, published_story)

    assert correct == 1
    assert total == 2


def test_get_post_reading_score_counts_true_values_in_post_reading_answers():
    progress = SessionProgressDTO(
        story_id=1,
        answers_given={
            'pre_reading': {},
            'post_reading': {
                '10': True,
                '11': False,
                '12': True,
            },
        },
    )

    correct, total = ReadingFlowService.get_post_reading_score(progress)

    assert correct == 2
    assert total == 3


# ========================
# 💾 Answer Mutation
# ========================

def test_set_pre_reading_answer_writes_into_pre_reading_bucket():
    progress = SessionProgressDTO(story_id=1)

    ReadingFlowService.set_pre_reading_answer(progress, 123, 'Stars')

    assert progress.answers_given == {
        'pre_reading': {'123': 'Stars'},
        'post_reading': {},
    }


def test_set_post_reading_answer_writes_into_post_reading_bucket_and_preserves_pre_reading_data():
    progress = SessionProgressDTO(
        story_id=1,
        answers_given={
            'pre_reading': {'5': 'Blue'},
            'post_reading': {},
        },
    )

    ReadingFlowService.set_post_reading_answer(progress, 77, True)

    assert progress.answers_given == {
        'pre_reading': {'5': 'Blue'},
        'post_reading': {'77': True},
    }
