import pytest

@pytest.mark.gjango_db
def test_session_progress_repository_return_dto(published_story) -> None:
    
    story = published_story
    