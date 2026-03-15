from abc import ABC, abstractmethod


class UserRepository(ABC):
    @abstractmethod
    def list_students(self) -> list:
        pass

    @abstractmethod
    def get_student(self, student_id: int):
        pass

    @abstractmethod
    def update_bio(self, user, bio: str):
        pass
