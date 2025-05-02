from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django import forms
from .models import Story, PreReadingExercise, PostReadingQuestion

# Form for user registration using the custom user model
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser  # Use your custom user model
        fields = ['username', 'password1', 'password2']  # Fields to include in the form

# Form used by teachers to create or edit stories
class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['title', 'description', 'content']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = False

# Form for creating and editing pre-reading exercises with validation logic
class PreReadingExerciseForm(forms.ModelForm):
    class Meta:
        model = PreReadingExercise
        fields = ['question_text', 'option_1', 'option_2', 'is_option_1_correct', 'is_option_2_correct', 'audio_file']

    def clean(self):
        cleaned_data = super().clean()
        option_1_correct = cleaned_data.get('is_option_1_correct')
        option_2_correct = cleaned_data.get('is_option_2_correct')

        # Ensure only one option is marked as correct
        if option_1_correct and option_2_correct:
            raise forms.ValidationError("You can only select one correct answer")
        # Ensure at least one option is marked as correct
        if not option_1_correct and not option_2_correct:
            raise forms.ValidationError("You must select one correct answer")
        
        return cleaned_data

# Form for creating and editing post-reading questions
class PostReadingQuestionForm(forms.ModelForm):
    class Meta:
        model = PostReadingQuestion
        fields = [
            'question_text',
            'option_1',
            'option_2',
            'option_3',
            'option_4',
            'correct_option',
            'explanation',
        ]
