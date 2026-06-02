# Task Manager

A Django-based task management system for daily productivity tracking.

Features:
- Add/edit/delete personal tasks
- Priorities and deadlines
- Completion status tracking
- User registration, login, and logout
- Responsive dashboard with deadline reminders

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\\Scripts\\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```
