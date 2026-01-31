# Antygravity Backend

A Django REST backend for the Antygravity mobile security app.

## Features

- **JWT Authentication** with email/password login
- **Social Login** (Google & Apple)
- **Parental Controls** - Child profiles, rules, and violation tracking
- **Network Monitoring** - Device discovery and scan logs
- **App Privacy Inspector** - Privacy scoring for installed apps

## Tech Stack

- Python 3.12
- Django 5.0
- Django REST Framework
- PostgreSQL
- Docker & Docker Compose

## Quick Start

### 1. Clone and Setup

```bash
cd antygravity_backend

# Copy environment file
cp .env.example .env

# Edit .env with your settings (especially GOOGLE_CLIENT_ID if needed)
```

### 2. Run with Docker

```bash
# Build and start services
docker compose up -d

# Check logs
docker compose logs -f web

# Run migrations (auto-runs on start, but if needed manually)
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
```

### 3. Access

- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login with email/password |
| POST | `/api/auth/token/refresh/` | Refresh JWT token |
| POST | `/api/auth/social/google/` | Google OAuth login |
| POST | `/api/auth/social/apple/` | Apple Sign-In |
| GET/PATCH | `/api/auth/me/` | User profile |

### Children & Parental Controls
| Method | Endpoint | Description |
|--------|----------|-------------|
| CRUD | `/api/children/` | Child profiles |
| CRUD | `/api/parental/rules/` | Parental rules |
| CRUD | `/api/parental/violations/` | Rule violations |

### Network Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| CRUD | `/api/network/devices/` | Network devices |
| POST | `/api/network/devices/{id}/mark_trusted/` | Mark device trusted |
| POST | `/api/network/devices/{id}/mark_blocked/` | Block device |
| CRUD | `/api/network/scans/` | Scan logs |

### Privacy
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/privacy/check/` | Run privacy check |
| GET | `/api/privacy/checks/` | List checks |

## Development

### Local Setup (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_HOST=localhost
# ... other vars

# Run migrations
python manage.py migrate

# Run server
python manage.py runserver
```

### Testing

```bash
# Run tests
docker compose exec web python manage.py test

# With coverage
docker compose exec web coverage run manage.py test
docker compose exec web coverage report
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (required) |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hostnames | `localhost,127.0.0.1` |
| `DATABASE_NAME` | PostgreSQL database name | `antygravity_db` |
| `DATABASE_USER` | PostgreSQL username | `antygravity_user` |
| `DATABASE_PASSWORD` | PostgreSQL password | (required) |
| `DATABASE_HOST` | PostgreSQL host | `db` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | (optional) |
| `APPLE_CLIENT_ID` | Apple Sign-In client ID | (optional) |

## License

Proprietary - All rights reserved.
