# Vike’s Reading App
**A Django web application for structured reading activities and student progress tracking.**

---

## 📚 Overview
**Vike’s Reading App** is an educational platform that helps **teachers assign structured reading tasks** and **track student progress** across three key stages:

1️⃣ **Pre-Reading** — Interactive exercises with audio and automatic progress tracking.  
2️⃣ **Reading** — Reading with time tracking.  
3️⃣ **Post-Reading** — Comprehension questions, limited story lookups (30s, 45s, 60s), and progress tracking.

---

## 👨‍🏫 User Roles & Permissions
| Role      | Actions                               |
|-----------|---------------------------------------|
| **Student** | Register, complete reading tasks, track personal progress |
| **Teacher** | Manage stories, view detailed student progress |

- **Teachers** are created via Django admin (`is_staff=True`).  
- **Students** self-register through the app.

Access control is enforced through **custom decorators** like:
- `@teacher_required`
- `@teacher_is_author`
- `@student_can_view_story`

---

## 🔧 How to Run Locally
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. (Optional) Create a superuser
python manage.py createsuperuser

# 4. Run the server
python manage.py runserver

# 5. Open in browser
http://127.0.0.1:8000/
```

---

## 🧑‍💻 Project Structure
```
vikes_reading_app/
├── models.py
├── forms.py
├── decorators.py   # Role-based access control
├── helpers.py      # Reusable helper functions
├── urls.py         # App-level routing
├── views/          # Modular views split by concern
│   ├── __init__.py
│   ├── auth.py
│   ├── home.py
│   ├── navigation.py
│   ├── post_reading.py
│   ├── pre_reading.py
│   ├── profile.py
│   ├── progress.py
│   ├── questions.py
│   ├── story_management.py
│   └── story_read.py
├── templates/vikes_reading_app/  # HTML templates
├── static/                       # CSS, JS, static files
├── media/                        # Uploaded audio files
├── tests/                        # Pytest files
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_decorators.py
│   ├── test_forms.py
│   ├── test_models.py
│   └── test_views.py
```

vikes_project/
├── __init__.py
├── asgi.py
├── settings.py
├── urls.py
└── wsgi.py

---

## ✅ Testing & Quality
**All core features are covered with Pytest:**
```bash
pytest
```
- **94 tests, 100% passing**
- Covers permissions, role access, CRUD, reading flows, and session logic.
- Modular views ensure clean, maintainable architecture.

---

## 🚀 Key Features for Employers
- Django best practices (views split by responsibility, DRY code via helpers).
- Role-based access enforced via custom decorators.
- Clean session management for tracking reading progress.
- Tested comprehensively with fixtures and parameterized tests.
- Modular, production-ready structure for scalability.
