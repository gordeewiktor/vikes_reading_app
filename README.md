# Vike's Reading App

Vike's Reading App is a Django-based web application designed to help students practice reading in a structured way.

Teachers create stories with pre-reading and post-reading questions, and students go through a guided learning flow while the app tracks their progress and time spent.

---

## 🧠 How it works

The app is built around a simple 3-step process:

- **Pre-reading** – students answer short questions and get immediate feedback  
- **Reading** – students read the story while the app tracks their time  
- **Post-reading** – students complete comprehension questions, with limited access to the story  

This flow is designed to simulate real classroom reading activities.

---

## ⚙️ Features

- User authentication with a custom user model  
- Two roles: **teacher** and **student**  
- Teachers can:
  - Create, edit, and delete stories  
  - Add pre-reading and post-reading questions  
  - View student progress  
- Students can:
  - Register and log in  
  - Choose a story and complete the full reading cycle  
- Pre-reading questions with two answer options and optional audio  
- Post-reading multiple-choice questions with explanations  
- Limited story lookup during post-reading (time-restricted per question)  
- Progress tracking per student and story (answers + time spent)  

---

## 🛠 Tech Stack

- Python  
- Django  
- SQLite (default)  
- Pytest  
- Django templates, forms, and ORM  

---

## How to run locally

```bash
# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# (Optional) Create admin user
python manage.py createsuperuser

# Run the server
python manage.py runserver