# IQRAA — Internship Management Platform

A Django REST Framework backend for managing internships, applications, and users with role-based access control (student, company, admin). Built for the IQRAA Mark Pvt Ltd Backend Developer Technical Assessment.

## Features

- **Role-based authentication** — Register and login with JWT tokens (student, company, admin roles)
- **Company profiles** — Create and manage company profiles linked to user accounts
- **Internship CRUD** — Companies can post, update, and delete internships with search, filter, and pagination
- **Application management** — Students can apply to internships with resume upload (PDF, max 2MB); companies can review and update application status
- **Rate limiting** — Custom IP-based rate limiter on the public listing endpoint (100 requests per 15 minutes)
- **Duplicate prevention** — Database-level unique_together constraint plus application-level pre-check to prevent duplicate applications
- **File uploads** — Resume upload with validation (PDF only, 2MB max)

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6.0.6 + Django REST Framework 3.17 |
| Database | PostgreSQL |
| Authentication | JWT (simplejwt) + bcrypt |
| File Storage | Local media folder |
| Environment | django-environ (.env) |

## Roles

| Role | Permissions |
|---|---|
| Student | Register, login, apply to internships, view own applications |
| Company | Register, login, post/manage internships, review applications, update status |
| Admin | Full access via Django admin panel |
