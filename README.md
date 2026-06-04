# IQRAA — Internship Management Platform

A Django REST Framework backend for connecting students with internship opportunities. Companies can post openings, students can apply with resumes, and admins oversee the process. Built with role-based access (student, company, admin), JWT authentication, and PostgreSQL.

---

## Quick Start

```bash
git clone https://github.com/abhikrishna-a/IQRAA.git
cd IQRAA
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
# create .env with your DB credentials (see below)
python manage.py migrate
python manage.py runserver
```

---

## Features

| Feature | Description |
|---|---|
| **Role-based auth** | Register as student, company, or admin. JWT tokens with 2h access / 7d refresh |
| **Company profiles** | Each company account has a detailed profile (name, description, website, logo) |
| **Internship CRUD** | Companies post internships with title, description, requirements, location, duration, and status |
| **Search & filter** | Public listing supports search (title/description/requirements), filter by status/location/company |
| **Pagination** | All list endpoints use page + limit params. Default: page 1, limit 10 |
| **Rate limiting** | 100 requests per 15 minutes per IP on the public internship listing |
| **Apply with resume** | Students submit applications with optional cover letter and resume (PDF only, max 2MB) |
| **Duplicate prevention** | unique_together constraint at DB level + pre-check in the view, returning 409 Conflict |
| **Status workflow** | Companies can accept or reject applications. Students see pending/accepted/rejected |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6.0.6 + Django REST Framework 3.17 |
| Database | PostgreSQL |
| Authentication | JWT (djangorestframework-simplejwt) + bcrypt password hashing |
| File storage | Local media/ folder (resumes, profile pictures, logos) |
| Environment | django-environ with .env file |

---

## Role System

| Role | Can do |
|---|---|
| **Student** | Register, login, update profile, apply to internships, view own applications |
| **Company** | Register, login, create company profile, post/edit/delete internships, review applications, update status |
| **Admin** | Django admin panel, full access to all data |

---

## API Endpoints

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register/ | None | Create account (username, email, password, role, phone) |
| POST | /api/auth/login/ | None | Get JWT access + refresh tokens |
| GET | /api/auth/profile/ | JWT | View your profile |
| PUT | /api/auth/profile/ | JWT | Update your profile (partial) |

**POST /api/auth/register/ example:**
```json
{
  "username": "jane",
  "email": "jane@example.com",
  "password": "securepass123",
  "role": "student",
  "phone": "+1234567890"
}
```
**Response:** 201 Created with id, username, email, role.

---

### Companies

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/companies/ | None | List all companies |
| POST | /api/companies/ | JWT | Create your company profile |
| GET | /api/companies/{id}/ | None | View company details |
| PUT | /api/companies/{id}/ | JWT* | Update company details |
| DELETE | /api/companies/{id}/ | JWT* | Delete company |

*Owner only — you must be the user linked to the company.

---

### Internships

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/internships/ | None | List all internships (paginated, rate-limited) |
| POST | /api/internships/ | JWT* | Post a new internship |
| GET | /api/internships/{id}/ | None | View internship details |
| PUT | /api/internships/{id}/ | JWT** | Full update |
| PATCH | /api/internships/{id}/ | JWT** | Partial update |
| DELETE | /api/internships/{id}/ | JWT** | Delete |

*Company role required
**Owner only — must be the company that posted it

**GET /api/internships/ query parameters:**

| Param | Example | Description |
|---|---|---|
| search | ?search=python | Searches title, description, requirements |
| status | ?status=open | Filter by open or closed |
| location | ?location=remote | Case-insensitive location filter |
| company_id | ?company_id=1 | Filter by company |
| page | ?page=2 | Page number (default: 1) |
| limit | ?limit=20 | Items per page (default: 10, max: none) |

**Response format:**
```json
{
  "count": 50,
  "page": 2,
  "limit": 10,
  "total_pages": 5,
  "results": [ ... ]
}
```

---

### Applications

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/applications/ | JWT | List applications (role-filtered) |
| POST | /api/applications/ | JWT* | Apply to an internship |
| GET | /api/applications/{id}/ | JWT** | View application details |
| PUT | /api/applications/{id}/status/ | JWT*** | Update application status |
| PATCH | /api/applications/{id}/status/ | JWT*** | Update application status |

*Student role only
**Owner only (student who applied or company that owns the internship)
***Company owner only (must own the internship)

**Role-based listing behavior:**
- **Student** — sees only their own applications
- **Company** — sees applications for their internships
- **Admin** — sees all applications

**POST /api/applications/ example (multipart/form-data):**
```
internship: 1
cover_letter: I am very interested in this position...
resume: [file upload, PDF only, max 2MB]
```

**Status values:** pending (default), accepted, rejected

---

## Testing

```bash
python manage.py test apps.internships.tests apps.applications.tests
```

**8 tests covering:**
- Internship pagination defaults and custom page/limit
- Rate limiting (429 after 100 requests)
- Resume upload (PDF accepted, non-PDF rejected)
- Application status update (invalid status, student denied, non-existent app)

---

## Database Overview

```
User (AbstractUser)
  - id (PK), username, email, password, role, phone, profile_picture
  - Index on email for fast login

Company
  - id (PK), user (O2O -> User), name, description, website, logo, location

Internship
  - id (PK), company (FK -> Company), title, description, requirements
  - location, duration, status (open/closed), created_at, updated_at

Application
  - id (PK), student (FK -> User), internship (FK -> Internship)
  - cover_letter, resume, status (pending/accepted/rejected)
  - applied_at, updated_at
  - unique_together: (student, internship)
```

---

## Project Structure

```
IQRAA/
├── IQRAA/
│   ├── settings/
│   │   ├── base.py          # Shared config (apps, auth, JWT, etc.)
│   │   ├── dev.py           # Development settings (PostgreSQL)
│   │   └── prod.py          # Production settings (PostgreSQL, DEBUG=False)
│   ├── __init__.py
│   ├── urls.py              # Root routing
│   ├── asgi.py
│   └── wsgi.py              # WSGI with IQRAA.settings.prod
├── apps/
│   ├── authentication/      # User model, register/login/profile views
│   ├── internships/         # Company & Internship models, CRUD views
│   └── applications/        # Application model, apply/list/status views
├── media/                   # Uploaded files (gitignored)
├── manage.py
├── requirements.txt
├── .env                     # Environment variables (gitignored)
└── .gitignore
```

---

## Environment Variables (.env)

```
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=iqraa
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```
