import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.create_superuser('admin@example.com', 'admin', 'password123')

refresh = RefreshToken.for_user(user)
print(str(refresh.access_token))
