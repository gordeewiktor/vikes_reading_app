Vike’s Reading App

Vike’s Reading App is an educational Django web application that helps teachers assign structured reading tasks and track student progress.

Students complete three stages:
	•	Pre-Reading → exercises with audio and automatic progress.
	•	Reading → reading the story with time tracking.
	•	Post-Reading → answering questions with correct answers tracking, limited story lookups (30s, 45s, 60s), and time spent tracking.

Teachers can view student progress on their profile page, including:
	•	Pre-Reading time
	•	Reading time
	•	Post-Reading score and time

⸻

How to Run
	1.	Install dependencies:
        pip install -r requirements.txt
    2.	Apply migrations:
        python manage.py migrate
    3.	(Optional) Create a superuser to access Django admin:
        python manage.py createsuperuser
    4.	Run the server:
        python manage.py runserver
    5.	Open the app in browser:
        http://127.0.0.1:8000/


User Roles
	•	Students → register directly, complete reading tasks.
	•	Teachers → created via Django admin (is_staff), can view student progress.

⸻


Project Structure
	• manage.py → Django project entry point
	• vikes_project/ → Django project settings and URLs
	• vikes_reading_app/ → Main app (models, views, templates)
	• media/ → Uploaded audio files
	• venv/ → Virtual environment (excluded from sharing)

