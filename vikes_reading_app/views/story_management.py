# --- Imports for Django views, models, forms, and decorators ---
from django.contrib import messages
from django.shortcuts import redirect, render
from vikes_reading_app.decorators import teacher_required, teacher_is_author
from vikes_reading_app.forms import StoryForm
from vikes_reading_app.models import Story
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository


# --- Views for Teacher Story Management ---
# These views allow teachers to create, edit, and delete their own stories,
# and ensure only authenticated teachers have access.

@teacher_required  # Ensures only logged-in teachers can access this view
def my_stories(request):
    """
    Shows a list of stories authored by the currently logged-in user.
    """
    # Filter stories so each teacher sees only their own authored stories
    stories = Story.objects.filter(author=request.user)
    return render(request, 'vikes_reading_app/my_stories.html', {'stories': stories})


@teacher_required  # Ensures only logged-in teachers can create stories
def story_create(request):
    repo = ORMStoryRepository()

    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            data["status"] = "published"  # enforce published status
            new_story = repo.create_story(request.user.id, data)
            messages.success(request, "Your story has been created!")
            return redirect('my_stories')
    else:
        form = StoryForm()

    return render(request, 'vikes_reading_app/story_create.html', {
        'form': form
    })


@teacher_is_author  # Ensures only the story's author can edit the story
def story_edit(request, story):
    """
    Allows authors to edit their own stories using repository pattern.
    """
    repo = ORMStoryRepository()  # Inject repository (could later be swapped with any implementation)

    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES, instance=story)
        if form.is_valid():
            # Use repository to perform update logic
            updated_story = repo.edit_story(story.id, form.cleaned_data)
            messages.success(request, "Your story has been updated!")
            return redirect('my_stories')
    else:
        form = StoryForm(instance=story)

    return render(request, 'vikes_reading_app/story_edit.html', {
        'form': form,
        'story': story,
    })


@teacher_is_author  # Ensures only the story's author can delete the story
def story_delete(request, story):
    """
    Allows authors to delete their own stories using repository pattern.
    """
    if request.method == 'POST':
        # Delete related exercises and questions before deleting the story itself to maintain data integrity
        repo = ORMStoryRepository()  # Inject repository
        repo.delete_story_with_related(story.id)
        messages.success(request, "Your story and related content have been deleted successfully!")
        return redirect('my_stories')

    return render(request, 'vikes_reading_app/story_delete.html', {'story': story})