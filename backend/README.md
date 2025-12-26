# EMIS - Educational Management Information System

A comprehensive assessment management system for informal sector skills assessment and certification.

## Project Structure

The system is built with Django REST Framework and organized into 13 modular apps:

### Core Apps

1. **users** - User management and authentication
2. **candidates** - Candidate registration and profile management
3. **occupations** - Occupation/trade definitions and units
4. **assessment_centers** - Assessment center and staff management
5. **assessment_series** - Assessment sessions and candidate registrations
6. **results** - Assessment results and final outcomes
7. **awards** - Certificate generation and management
8. **reports** - System reporting functionality
9. **complaints** - Complaint and appeal handling
10. **uvtab_fees** - Fee structures and payment processing
11. **statistics** - System-wide statistics tracking
12. **configurations** - System configurations and email templates
13. **dit_migration** - Legacy data migration from old DIT system

## Setup Instructions

### Prerequisites

- Python 3.12+
- PostgreSQL (recommended) or SQLite for development
- Redis (for Celery tasks)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd "/home/claire/Desktop/projects/informal system"
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server:**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

All apps expose RESTful API endpoints under `/api/`:

- `/api/users/` - User management
- `/api/candidates/` - Candidate operations
- `/api/occupations/` - Occupation management
- `/api/assessment-centers/` - Center management
- `/api/assessment-series/` - Assessment series
- `/api/results/` - Results management
- `/api/awards/` - Certificate management
- `/api/reports/` - Report generation
- `/api/complaints/` - Complaint handling
- `/api/uvtab-fees/` - Fee and payment management
- `/api/statistics/` - Statistics
- `/api/configurations/` - System configuration
- `/api/dit-migration/` - Migration tools

## Admin Panel

Access the Django admin panel at `/admin/` with superuser credentials.

## Development Guidelines

### App Independence

Each app is designed to be independent with:
- Its own models, views, serializers, and URLs
- Minimal cross-app dependencies
- Clear API boundaries

### Adding New Features

1. Identify the appropriate app
2. Add models in `models.py`
3. Create serializers in `serializers.py`
4. Define views in `views.py`
5. Register URLs in `urls.py`
6. Add admin interface in `admin.py`
7. Run migrations

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

## Technology Stack

- **Backend Framework:** Django 5.0
- **API Framework:** Django REST Framework
- **Database:** PostgreSQL (production) / SQLite (development)
- **Task Queue:** Celery + Redis
- **Authentication:** Django Auth + JWT (to be added)
- **File Storage:** Local (development) / Cloud (production)

## Next Steps

1. Set up frontend (React/Next.js recommended)
2. Implement JWT authentication
3. Add comprehensive tests
4. Set up CI/CD pipeline
5. Configure production deployment
6. Implement real-time notifications
7. Add data export/import features

## License

Proprietary - All rights reserved
