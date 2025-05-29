import pytest
from vikes_reading_app.forms import CustomUserCreationForm

@pytest.mark.django_db  # Allows test to interact with the database
def test_user_registration_form_valid():
    # Simulate user input data for registration
    form_data = {
        "username": "testuser",
        "password1": "strongpassword123",  # Password field 1
        "password2": "strongpassword123"   # Password field 2 (must match)
    }

    # Create the registration form with the input data
    form = CustomUserCreationForm(data=form_data)

    # Assert that the form is valid (i.e., passwords match, username is acceptable)
    assert form.is_valid()