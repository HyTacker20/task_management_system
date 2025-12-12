# Task Management System

A Django-based task management system with Celery for background processing and automatic task distribution.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd task_management_system
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL database (port 5432)
   - Redis (port 6379)
   - Django web server (port 8000)
   - Celery worker
   - Celery beat scheduler

3. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Create a superuser (optional)**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - API Documentation: http://localhost:8000/api/schema/swagger-ui/

## Common Commands

**View logs**
```bash
docker-compose logs -f web
docker-compose logs -f celery_worker
```

**Stop services**
```bash
docker-compose down
```

**Restart a service**
```bash
docker-compose restart web
```

**Run tests**
```bash
docker-compose exec web pytest
```

**Load fixtures**
```bash
docker-compose exec web python manage.py loaddata fixtures.json
```

## Tech Stack

- Django 5.1.3
- Django REST Framework 3.15.2
- PostgreSQL 16
- Redis 7
- Celery 5.4.0

## Development

The project uses volumes for hot-reloading, so code changes will automatically restart the Django development server.