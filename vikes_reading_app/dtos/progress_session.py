from dataclasses import dataclass, field

@dataclass
class SessionProgressDTO:
    story_id: int
    score: float = 0.0
    answers_given: dict = field(default_factory=dict)
    current_stage: str = "pre_reading"
    pre_reading_time: int = 0
    post_reading_time: int = 0

    @property
    def is_empty(self) -> bool:
        """
        Determines if this progress represents no real progress.
        """
        return self.current_stage == "pre_reading" and not self.answers_given