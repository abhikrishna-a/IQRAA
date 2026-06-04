# IQRAA — Internship Management Platform

A Django REST Framework backend for managing internships, applications, and users with role-based access control (student, company, admin). Built for the IQRAA Mark Pvt Ltd Backend Developer Technical Assessment.

## Features

- **Role-based authentication** — Register and login with JWT tokens (student, company, admin roles)
- **Company profiles** — Create and manage company profiles linked to user accounts
- **Internship CRUD** — Companies can post, update, and delete internships with search, filter, and pagination
- **Application management** — Students can apply to internships with resume upload (PDF, max 2MB); companies can review and update application status
- **Rate limiting** — Custom IP-based rate limiter on the public listing endpoint (100 requests per 15 minutes)
- **Duplicate prevention** — Database-level `unique_together` constraint plus application-level pre-check to prevent duplicate applications
- **File uploads** — Resume upload with validation (PDF only, ≤ 2MB)

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6.0.6 + Django REST Framework 3.17 |
| Database | PostgreSQL |
| Auth | JWT (djangorestframework-simplejwt) with bcrypt password hashing |
| File Storage | Local media folder (media/) |
| Environment | django-environ (.env file) |

## ERD Overview

```
User (AbstractUser)
  ├── role: student | company | admin
  ├── email (indexed)
  │
  ├── Company (OneToOne) ──→ Internship (FK)
  │                              ├── title, description, requirements
  │                              ├── location, duration, status
  │                              └── created_at, updated_at
  │
  └── Application (FK) ──→ Internship (FK)
       ├── cover_letter, resume (PDF only)
       ├── status: pending | accepted | rejected
       ├── applied_at, updated_at
       └── unique_together: (student, internship)
```




### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | /api/auth/register/ | Register a new user | None |
| POST | /api/auth/login/ | Login, returns JWT access + refresh | None |
| GET | /api/auth/profile/ | Get authenticated user's profile | JWT |
| PUT | /api/auth/profile/ | Update profile (partial) | JWT |

### Companies

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | /api/companies/ | List all companies | None |
| POST | /api/companies/ | Create a company profile | JWT |
| GET | /api/companies/{id}/ | Company detail | None |
| PUT | /api/companies/{id}/ | Update company (owner only) | JWT |
| DELETE | /api/companies/{id}/ | Delete company (owner only) | JWT |

### Internships

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | /api/internships/ | List internships (paginated, rate-limited) | None |
| POST | /api/internships/ | Create internship (company only) | JWT |
| GET | /api/internships/{id}/ | Internship detail | None |
| PUT | /api/internships/{id}/ | Full update (owner only) | JWT |
| PATCH | /api/internships/{id}/ | Partial update (owner only) | JWT |
| DELETE | /api/internships/{id}/ | Delete (owner only) | JWT |

**Query parameters for GET /api/internships/:**
- `search` — search title, description, requirements (icontains)
- `status` — filter by open/closed
- `location` — filter by location (case-insensitive)
- `company_id` — filter by company
- `page` — page number (default: 1)
- `limit` — items per page (default: 10)

### Applications

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | /api/applications/ | List applications (role-based) | JWT |
| POST | /api/applications/ | Apply for internship (student only) | JWT |
| GET | /api/applications/{id}/ | Application detail (owner only) | JWT |
| PUT | /api/applications/{id}/status/ | Update status (company owner only) | JWT |
| PATCH | /api/applications/{id}/status/ | Update status (company owner only) | JWT |

**Role-based listing behavior:**
- **Student** — sees only their own applications
- **Company** — sees applications for their internships
- **Admin** — sees all applications

## Project Structure

```
IQRAA/
├── IQRAA/
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── dev.py           # Development settings
│   │   └── prod.py          # Production settings
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI entry point
├── apps/
│   ├── authentication/      # User model, register, login, profile
│   ├── internships/         # Company, Internship models + CRUD
│   └── applications/        # Application model + apply/list/status
├── manage.py
├── requirements.txt
└── .env
```
