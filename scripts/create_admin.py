import os
import sys
import pathlib
import secrets

# Ensure project root is on sys.path so Django can be imported when running this script
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_system.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

existing = User.objects.filter(is_superuser=True)
if existing.exists():
    print('Superuser(s) already exist:')
    for u in existing:
        print(f'- {u.username} (email: {u.email})')
else:
    username = 'admin'
    email = 'admin@example.com'
    password = secrets.token_urlsafe(12)
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Created superuser:')
    print(f'  username: {username}')
    print(f'  email: {email}')
    print(f'  password: {password}')
    print('\nPlease change this password after logging in: /admin/auth/user/')
