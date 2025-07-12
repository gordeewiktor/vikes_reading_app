from vikes_reading_app.models import Story, PostReadingQuestion, PreReadingExercise
from django.shortcuts import redirect, render
from vikes_reading_app.forms import StoryForm
from django.contrib import messages
from vikes_reading_app.decorators import teacher_required, teacher_is_author

@teacher_required
def my_stories(request):
    """
    Shows a list of stories authored by the currently logged-in user.
    """
    stories = Story.objects.filter(author=request.user)
    return render(request, 'vikes_reading_app/my_stories.html', {'stories': stories})
    
    
@teacher_required
def story_create(request):
    """
    Allows teachers to create a new story.
    On POST, saves the story as 'published' and redirects to 'my_stories'.
    """
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.author = request.user
            story.status = 'published'
            messages.success(request, "Your story has been published!")
            story.save()
            return redirect('my_stories')
    else:
        form = StoryForm()
    return render(request, 'vikes_reading_app/story_create.html', {'form': form})

@teacher_is_author
def story_edit(request, story):
    """
    Allows authors to edit their own stories.
    On POST, updates the story and redirects to 'my_stories'.
    """
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES, instance=story)
        if form.is_valid():
            story = form.save(commit=False)
            story.status = 'published'
            story.save()
            messages.success(request, "Your story has been updated!")
            return redirect('my_stories')
    else:
        form = StoryForm(instance=story)
    return render(request, 'vikes_reading_app/story_edit.html', {
        'form': form,
        'story': story
    })

@teacher_is_author
def story_delete(request, story):
    """
    Allows authors to delete their own stories.
    On POST, deletes the story and all related exercises/questions.
    """
    if request.method == 'POST':
        PreReadingExercise.objects.filter(story=story).delete()
        PostReadingQuestion.objects.filter(story=story).delete()
        story.delete()
        messages.success(request, "Your story and related content have been deleted successfully!")
        return redirect('my_stories')
    return render(request, 'vikes_reading_app/story_delete.html', {'story': story})