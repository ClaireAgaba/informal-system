# EMIS Development Guide

## Getting Started

### Initial Setup

1. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration.

2. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   Or manually:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Start development server:**
   ```bash
   python manage.py runserver
   ```

## App Development Order

Based on dependencies, develop apps in this order:

### Phase 1: Foundation (Completed ✓)
1. **users** - Base authentication and user management
2. **configurations** - System settings and email templates

### Phase 2: Core Entities
3. **candidates** - Candidate profiles
4. **occupations** - Trades and units
5. **assessment_centers** - Centers and staff

### Phase 3: Assessment Management
6. **assessment_series** - Assessment sessions and registrations
7. **uvtab_fees** - Fee structures and payments

### Phase 4: Results & Awards
8. **results** - Assessment results and final outcomes
9. **awards** - Certificate generation

### Phase 5: Support Features
10. **complaints** - Complaint handling
11. **reports** - Report generation
12. **statistics** - System statistics

### Phase 6: Migration
13. **dit_migration** - Legacy data migration

## Working on an App

### 1. Define Models

```python
# app_name/models.py
from django.db import models

class YourModel(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'
    
    def __str__(self):
        return self.name
```

### 2. Create Serializers

```python
# app_name/serializers.py
from rest_framework import serializers
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = '__all__'
        read_only_fields = ['created_at']
```

### 3. Define Views

```python
# app_name/views.py
from rest_framework import viewsets, permissions
from .models import YourModel
from .serializers import YourModelSerializer

class YourModelViewSet(viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['field1', 'field2']
    search_fields = ['name']
```

### 4. Register URLs

```python
# app_name/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.YourModelViewSet, basename='your-model')

urlpatterns = [
    path('', include(router.urls)),
]
```

### 5. Configure Admin

```python
# app_name/admin.py
from django.contrib import admin
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']
```

### 6. Run Migrations

```bash
python manage.py makemigrations app_name
python manage.py migrate
```

## Common Development Tasks

### Adding a New Field to a Model

1. Add field to model
2. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Adding Custom API Endpoint

```python
# In your ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

@action(detail=True, methods=['post'])
def custom_action(self, request, pk=None):
    obj = self.get_object()
    # Your logic here
    return Response({'status': 'success'})
```

### Adding Filtering

```python
# Install django-filter (already in requirements.txt)
# In your ViewSet
from django_filters import rest_framework as filters

class YourModelFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    
    class Meta:
        model = YourModel
        fields = ['name', 'created_after']

class YourModelViewSet(viewsets.ModelViewSet):
    filterset_class = YourModelFilter
```

### Adding Custom Permissions

```python
# app_name/permissions.py
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

# In your ViewSet
from .permissions import IsOwnerOrReadOnly

class YourModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
```

## Testing

### Writing Tests

```python
# app_name/tests.py
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import YourModel

User = get_user_model()

class YourModelTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_model(self):
        data = {'name': 'Test'}
        response = self.client.post('/api/your-app/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_list_models(self):
        response = self.client.get('/api/your-app/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test app_name

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Database Management

### Creating Migrations

```bash
# Create migrations for all apps
python manage.py makemigrations

# Create migration for specific app
python manage.py makemigrations app_name

# Create empty migration (for data migrations)
python manage.py makemigrations --empty app_name
```

### Applying Migrations

```bash
# Apply all migrations
python manage.py migrate

# Apply migrations for specific app
python manage.py migrate app_name

# Show migration status
python manage.py showmigrations
```

### Database Shell

```bash
# Django shell
python manage.py shell

# Database shell
python manage.py dbshell
```

## Useful Django Commands

### Create Superuser
```bash
python manage.py createsuperuser
```

### Collect Static Files
```bash
python manage.py collectstatic
```

### Clear Cache
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Load Fixtures
```bash
python manage.py loaddata fixture_name
```

### Dump Data
```bash
python manage.py dumpdata app_name > fixture.json
```

## API Testing

### Using cURL

```bash
# Get list
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/app-name/

# Create
curl -X POST -H "Authorization: Token YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name":"Test"}' \
     http://localhost:8000/api/app-name/

# Update
curl -X PUT -H "Authorization: Token YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name":"Updated"}' \
     http://localhost:8000/api/app-name/1/
```

### Using Python Requests

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login/', 
                        json={'username': 'user', 'password': 'pass'})
token = response.json()['token']

# Make authenticated request
headers = {'Authorization': f'Token {token}'}
response = requests.get('http://localhost:8000/api/app-name/', headers=headers)
```

## Code Style

### Follow PEP 8
```bash
# Install flake8
pip install flake8

# Check code
flake8 .
```

### Format Code
```bash
# Install black
pip install black

# Format code
black .
```

## Git Workflow

### Branch Naming
- `feature/app-name-feature-description`
- `bugfix/app-name-bug-description`
- `hotfix/critical-issue-description`

### Commit Messages
```
[APP_NAME] Brief description

Detailed explanation of changes
- Change 1
- Change 2

Closes #issue_number
```

## Debugging

### Django Debug Toolbar
```bash
pip install django-debug-toolbar
```

Add to `settings.py`:
```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.debug('Debug message')
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message')
```

## Performance Optimization

### Database Queries
```python
# Use select_related for foreign keys
queryset = Model.objects.select_related('foreign_key_field')

# Use prefetch_related for many-to-many
queryset = Model.objects.prefetch_related('many_to_many_field')

# Add indexes in models
class Meta:
    indexes = [
        models.Index(fields=['field_name']),
    ]
```

### Caching
```python
from django.core.cache import cache

# Set cache
cache.set('key', 'value', timeout=300)

# Get cache
value = cache.get('key')

# Delete cache
cache.delete('key')
```

## Next Steps

1. Set up frontend application (React/Next.js)
2. Implement JWT authentication
3. Add comprehensive tests for each app
4. Set up CI/CD pipeline
5. Configure production deployment
6. Implement real-time features
7. Add monitoring and logging

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
