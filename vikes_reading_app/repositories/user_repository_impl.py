from django.shortcuts import get_object_or_404

from vikes_reading_app.models import CustomUser
from .user_repository import UserRepository


class ORMUserRepository(UserRepository):
    def list_students(self) -> list:
        return CustomUser.objects.filter(role='student')

    def get_student(self, student_id: int):
        return get_object_or_404(CustomUser, id=student_id, role='student')

    def update_bio(self, user, bio: str):
        user.bio = bio
        user.save()
        return user
