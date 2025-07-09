import pytest
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from vikes_reading_app.decorators import teacher_required
from django.http import HttpResponse

@pytest.fixture
def factory():
    return RequestFactory()

def dummy_view(request):
    return HttpResponse("OK")

def test_teacher_required_allows_teacher(factory, teacher_user):
    request = factory.get('/')
    request.user = teacher_user

    wrapped_view = teacher_required(dummy_view)
    response = wrapped_view(request)

    assert response.status_code == 200
    assert response.content == b"OK"

def test_teacher_required_redirects_student(factory, student_user):
    request = factory.get('/')
    request.user = student_user

    wrapped_view = teacher_required(dummy_view)
    response = wrapped_view(request)

    assert response.status_code == 302
    assert response.url == '/profile/'

def test_teacher_required_redirects_anonymous(factory):
    request = factory.get('/')
    request.user = AnonymousUser()

    wrapped_view = teacher_required(dummy_view)
    response = wrapped_view(request)

    assert response.status_code == 302
    assert response.url == '/login/'