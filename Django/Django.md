# Django

<details><summary style="font-size: 1.5em;">Django Project Structure</summary>

```
myproject/
│
├── manage.py
│
├── myproject/                # Project configuration package
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── myapp/                    # Django app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── tests.py
│   ├── serializers.py        # (If using DRF)
│   ├── migrations/
│   │   └── __init__.py
│   │
│   ├── templates/
│   │   └── myapp/
│   │       └── example.html
│   │
│   └── static/
│       └── myapp/
│           ├── css/
│           ├── js/
│           └── images/
│
├── media/                    # User uploaded files
│
├── static/                   # (Optional global static folder)
│
└── db.sqlite3                # Default database
```
</details>

## Project Structure & Configuration
Project   
App   
manage.py   
Settings   
WSGI / ASGI   

## Routing & Request Handling
URL Dispatcher (URLs / Routing)   
Middleware   
Sessions   
   
## Views Layer   
Views   
Function-Based Views (FBVs)   
Class-Based Views (CBVs)   
API Views (DRF)   
ViewSets (DRF)   
Routers (DRF)   
   
## Templates & Frontend Integration   
Templates   
Template Tags & Filters   
Context Processors   
Static Files   
Media Files   
   
## Database Layer   
Models   
ORM (Object Relational Mapper)   
Migrations   
QuerySets   
Managers   
   
## Forms & User Input   
Forms   
ModelForms   
   
## Authentication & Authorization   
Authentication   
Authorization (Permissions & Groups)   
   
## Admin & Management   
Admin Site   
Management Commands   
Fixtures   
   
## API & Serialization (Django REST Framework)   
REST Framework (DRF)   
Serializers   
   
## Real-Time & Async   
Channels (WebSockets)   
   
## Testing   
Testing (TestCase)   

## CLI Commands
```bash
python3 -m venv .venv
django-admin startproject <PROJECT_NAME> <PROJECT_LOCATION>
django-admin startapp <APP_NAME>
python manage.py runserver
```

## References
[Youtube (1hr): NeuralNine - Django Full Crash Course - The Professional Python Web Framework](https://www.youtube.com/watch?v=u1GnZfDw5LU)

[Youtube (3hr): Tech With Tim - Django For Beginners - Full Tutorial](https://www.youtube.com/watch?v=sm1mokevMWk)

[Youtube (7hr): Traversy Media - Python Django 7 Hour Course](https://www.youtube.com/watch?v=PtQiiknWUcI)

