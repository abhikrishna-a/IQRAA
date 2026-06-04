# IQRAA — Internship Management Platform

Django REST Framework backend for managing internships, applications, and users with role-based access (student, company, admin).

## Tech Stack

- **Python 3.12+** / **Django 6.0.6**
- **Django REST Framework** 3.17
- **PostgreSQL** (production & development)
- **JWT Authentication** (djangorestframework-simplejwt)
- **bcrypt** password hashing
- **Cloudinary / Pillow** for image uploads

## Quick Start

```bash
git clone https://github.com/abhikrishna-a/IQRAA.git
cd IQRAA
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in your secrets
python manage.py migrate
python manage.py runserver
```

## API Endpoints

```
POST   /api/auth/register/                     Register user
POST   /api/auth/login/                        Login, returns JWT
GET    /api/auth/profile/                      Get profile
PUT    /api/auth/profile/                      Update profile

GET    /api/companies/                         List companies
POST   /api/companies/                         Create company
GET    /api/companies/<id>/                    Company detail
PUT    /api/companies/<id>/                    Update company (owner)
DELETE /api/companies/<id>/                    Delete company (owner)

GET    /api/internships/                       List (public, paginated, rate-limited)
POST   /api/internships/                       Create (company only)
GET    /api/internships/<id>/                  Detail
PUT    /api/internships/<id>/                  Full update (owner)
PATCH  /api/internships/<id>/                  Partial update (owner)
DELETE /api/internships/<id>/                  Delete (owner)

GET    /api/applications/                      List (role-based)
POST   /api/applications/                      Apply (student only)
GET    /api/applications/<id>/                 Detail (owner only)
PUT    /api/applications/<id>/status/          Update status (company only)
PATCH  /api/applications/<id>/status/          Update status (company only)
```

---

## Technical Assessment Answers

### SECTION C — Scalability & Problem Solving

#### 1. Handling 50,000 applications in 1 hour

**Already implemented:**
- Pagination (`page` & `limit` params) caps result set sizes — `apps/internships/views.py:121-127`
- `select_related()` on all FK relationships eliminates N+1 queries — e.g., `apps/applications/views.py:47-49`
- Rate limiting (100 req/15 min per IP) protects the listing endpoint — `apps/internships/views.py:18-31`
- JWT stateless auth means any server instance can handle any request

**Would add in production:**
- **Load balancer** (AWS ALB / Nginx) to distribute traffic across multiple gunicorn instances
- **Auto-scaling groups** to spin up instances based on CPU/memory
- **Gunicorn workers** = (2 × CPU cores) + 1 per instance
- **PgBouncer** for database connection pooling
- **CDN** (CloudFront) for static/media assets

#### 2. Indexes

**Already in the project:**
| Index | Location | Purpose |
|---|---|---|
| `User.email` | `apps/authentication/models.py:18` | Fast login lookups |
| `Application(student, internship)` | `apps/applications/models.py:21` | Unique constraint + duplicate check |

**Would add for high traffic:**
```python
# apps/applications/models.py — additional indexes
class Meta:
    indexes = [
        models.Index(fields=['internship']),           # company application listing
        models.Index(fields=['student']),               # student's own applications
        models.Index(fields=['internship', 'status']),  # filter pending by internship
    ]

# apps/internships/models.py
class Meta:
    indexes = [
        models.Index(fields=['status']),                # filter open/closed
        models.Index(fields=['company']),               # company internship listing
    ]
```

#### 3. Response time < 500ms

**Already implemented:**
- `select_related()` on all view queries to prevent N+1 — `apps/internships/views.py:101`, `apps/applications/views.py:47`
- Pagination ensures no endpoint returns unbounded result sets
- `raise_exception=True` on all serializers fails fast on bad input

**Would add:**
- **Redis cache** for `GET /api/internships/` — cache key `internships:page:{n}:limit:{l}`, TTL 30-60s, invalidate on create/update/delete
- **Database read replicas** — route SELECTs to replica, primary handles only writes
- **Query timeout** — `CONN_MAX_AGE` + statement timeout to prevent long queries blocking the pool

#### 4. Preventing duplicate applications

Already has two layers of defense:

1. **View-level pre-check:** `Application.objects.filter(student=user, internship_id=id).exists()` — `apps/applications/views.py:22`
2. **Database constraint:** `unique_together = ('student', 'internship')` — `apps/applications/models.py:21`

Under race conditions the DB constraint is the source of truth. If two concurrent requests pass the pre-check simultaneously, the second insert hits `IntegrityError` which is caught and returned as `409 Conflict` — `apps/applications/views.py:28-30`.

#### 5. Redis usage

Not currently implemented. Would add:

| Use Case | Implementation |
|---|---|
| **Cache** | Cache paginated internship listings with short TTL (30-60s) |
| **Rate limiting** | Replace current in-memory `RATE_LIMIT` dict (in `apps/internships/views.py:13-31`) with `django-ratelimit` + Redis backend — works across multiple workers |
| **Session store** | Django session backend backed by Redis |
| **Queue broker** | Celery broker for async tasks |

```python
# settings/base.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

#### 6. Queue systems (Celery / RabbitMQ / Kafka)

Not currently implemented. Would add **Celery + Redis** for:

- **Confirmation emails** after application submission (send async, API responds 201 immediately)
- **Status change notifications** when a company accepts/rejects an application
- **Resume virus scanning** — upload accepted, scan queued in background
- Kafka would be considered if the platform later needs event streaming for analytics or audit logs

#### 7. Scaling strategy

| Layer | Strategy |
|---|---|
| **Application** | Horizontal scaling — stateless JWT auth means any instance handles any request. Docker + Kubernetes for orchestration |
| **Database** | Read replicas for SELECT workloads. Shard by `company_id` if dataset grows beyond hundreds of millions of rows |
| **Media** | Serve resumes/images from S3 + CloudFront, not through Django |
| **Monitoring** | Prometheus + Grafana for metrics, Sentry for errors, structured JSON logging to ELK |

---

### SECTION D — Query Optimization

Given the query:
```sql
SELECT * FROM applications WHERE internship_id = 100 ORDER BY created_at DESC;
```
on a table with 10M+ records.

#### 1. Why it's slow

- **No index on `internship_id`** — full table scan reads all 10M rows
- **No index on `created_at`** — PostgreSQL must sort the entire result set (filesort, O(n log n))
- **`SELECT *`** — retrieves all columns, increasing I/O and network cost
- **No `LIMIT`** — materialises every matching row

#### 2. How to optimise

**Step 1 — Composite index (covers WHERE + ORDER BY in one scan):**
```python
# apps/applications/models.py
class Meta:
    indexes = [
        models.Index(
            fields=['internship_id', '-created_at'],
            name='app_internship_created_idx'
        ),
    ]
```

**Step 2 — Select only needed columns and paginate:**
```python
Application.objects.filter(internship_id=100) \
    .only('id', 'student_id', 'status', 'created_at') \
    .order_by('-created_at')[:20]
```

**Step 3 — Cursor-based pagination for deep pages** — use `created_at` + `id` as a keyset cursor instead of `OFFSET`, which degrades on large offsets.

#### 3. Recommended indexes on Application

```python
class Meta:
    unique_together = ('student', 'internship')  # already present
    indexes = [
        models.Index(fields=['internship_id', '-created_at']),
        models.Index(fields=['student_id']),
        models.Index(fields=['internship_id', 'status']),
    ]
```

#### 4. Measuring improvement

- **`EXPLAIN ANALYZE`** — compare execution plans before/after: `Seq Scan` → `Index Only Scan`
- **pg_stat_statements / pgBadger** — monitor slow queries in production
- **`locust` / `k6`** — load test with 50,000 concurrent users, measure p95/p99 latency
- **Django Silk** — profile ORM queries during development
