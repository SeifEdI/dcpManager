# My App

This application allows to manage all ressources in DCP service

## Tech stack
Django + python 

## How to run

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python scripts/init_database.py
python scripts/create_departments.py
python scripts/init_rbac.py
python scripts/init_audit.py

python3 manage.py runserver
