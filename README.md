# IQRAA Mark Pvt Ltd — Backend Developer Technical Assessment
## Sections C & D — Model Answers

---

### SECTION C — Scalability & Problem Solving (20 Marks)

#### Question 3
Scenario: 1,000 internships are published. Within 1 hour, 50,000 students apply.

---

**1. How will your system handle this traffic?**

Deploy the Django application behind a load balancer (e.g., AWS ALB or Nginx) distributing requests across multiple application server instances (gunicorn workers).
Use auto-scaling groups so new instances spin up automatically when CPU/memory thresholds are exceeded.
Configure gunicorn with multiple workers per instance: `workers = (2 × CPU cores) + 1`.
Put a CDN (e.g., CloudFront) in front of static assets to reduce load on the origin.
Enable connection pooling (PgBouncer) to prevent the database from being overwhelmed by too many simultaneous connections.

---

**2. What indexes will you create?**

The following indexes directly speed up the most common queries under high load:

- `applications(student_id, internship_id)` — already enforced by `unique_together`, covers duplicate-check lookups.
- `applications(internship_id)` — for companies fetching all applications for a given internship.
- `applications(student_id)` — for students listing their own applications.
- `internships(status)` — for filtering open/closed listings.
- `internships(company_id)` — for company-scoped internship queries.
- `users(email)` — already added; speeds up login lookups.

```python
class Meta:
    indexes = [
        models.Index(fields=['student', 'internship']),
        models.Index(fields=['internship']),
        models.Index(fields=['status']),
    ]
```

---

**3. How will you keep response time below 500ms?**

- Use `select_related()` and `prefetch_related()` on all views that touch FK/M2M relations to eliminate N+1 queries.
- Cache the internship listing (the most-read endpoint) in Redis with a short TTL (30–60 seconds). A listing serving 50,000 reads/hour does not need a fresh DB hit every time.
- Use database read replicas — route all SELECT queries to a replica so the primary only handles writes.
- Paginate all list endpoints (already implemented — page + limit params) to cap result set sizes.
- Use Django Debug Toolbar in development to profile slow queries before they reach production.
- Set database query timeouts to prevent long-running queries from blocking the connection pool.

---

**4. How will you prevent duplicate applications?**

- Database-level constraint: `unique_together = ('student', 'internship')` on the Application model ensures the DB enforces uniqueness even under race conditions.
- Application-level pre-check: The view checks `Application.objects.filter(student=user, internship_id=id).exists()` before attempting to insert, returning `409 Conflict` early.
- Double defense: Both checks are in place — the pre-check avoids wasted DB insert attempts; the unique constraint is the final safety net.
- Under high concurrency, the DB constraint is the only truly reliable guard — two concurrent requests can both pass the pre-check before either commits. The `IntegrityError` from the DB is caught and returned as `409`.

---

**5. Will you use Redis? How?**

Yes. Redis serves multiple roles:

- **Cache Layer:** Cache the paginated internship list results. Key pattern: `internships:page:{n}:limit:{l}:status:{s}`. Invalidate on any internship create/update/delete.
- **Rate Limiting:** Replace the current in-memory `RATE_LIMIT` dict with Redis-backed counters (`django-ratelimit` with Redis backend). This works correctly across multiple application server instances, unlike the current dict which is per-process.
- **Session Store:** Use Redis as the Django session backend for fast session reads.
- **Queue Broker:** Use Redis as the Celery message broker for async tasks (e.g., sending confirmation emails after application submission).

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

---

**6. Will you use Queue Systems (RabbitMQ / Kafka)?**

Yes — Celery with Redis or RabbitMQ as the broker for async tasks that should not block the API response:

- **Application confirmation email:** After a student applies, the API responds 201 immediately. A Celery task sends the confirmation email in the background.
- **Status change notification:** When a company updates an application status to accepted or rejected, a Celery task notifies the student via email/push.
- **Resume virus scan:** Upload the resume, respond 201, then queue a background task to scan the file.

Kafka would be preferred if the platform later needs event streaming (e.g., analytics pipeline, audit log). For this scale, Celery + Redis/RabbitMQ is sufficient.

---

**7. How will you scale the system?**

- **Horizontal Scaling:** Add more application server instances behind the load balancer. Stateless design (JWT auth, no server-side sessions) means any instance can handle any request.
- **Database Scaling:** Add read replicas for SELECT-heavy workloads. Consider sharding by `company_id` if the dataset grows beyond hundreds of millions of rows.
- **Microservices (future):** Split authentication, internships, and applications into separate services if team size and deployment cadence require it.
- **Container Orchestration:** Dockerise each service and deploy on Kubernetes (EKS/GKE) for auto-healing, rolling deployments, and resource efficiency.
- **CDN:** Serve media files (resumes, profile pictures, logos) directly from S3 + CloudFront rather than through Django.
- **Observability:** Add Prometheus + Grafana for metrics, Sentry for error tracking, and structured logging (JSON logs to ELK/CloudWatch) so bottlenecks are detected before they become outages.

---

### SECTION D — Query Optimization (10 Marks)

#### Question 4

Given query:
```sql
SELECT *
FROM applications
WHERE internship_id = 100
ORDER BY created_at DESC;
```
The applications table contains more than 10 million records.

---

**1. Why is the query slow?**

- **Full table scan:** Without an index on `internship_id`, PostgreSQL must read all 10M+ rows to find those matching `internship_id = 100`.
- **No index on ORDER BY column:** Sorting 10M rows by `created_at` without an index requires an in-memory or on-disk sort operation (filesort), which is O(n log n).
- **SELECT \*:** Fetching all columns causes wider rows to be transferred — many columns that are never used add network and memory overhead.
- **Large result set:** Even after filtering, if internship 100 has thousands of applications, returning all of them in one query is expensive.
- **No LIMIT:** Without pagination, the DB must materialise the entire result set before returning it.

---

**2. How do you optimize it?**

**Step 1 — Add a composite index:**
```sql
CREATE INDEX idx_applications_internship_created
ON applications (internship_id, created_at DESC);
```
This is a covering index for the WHERE + ORDER BY. PostgreSQL can satisfy both clauses by scanning the index alone (Index Only Scan), touching zero heap pages for rows that fit in memory.

**Step 2 — Select only needed columns:**
```sql
SELECT id, student_id, cover_letter, status, resume, created_at
FROM applications
WHERE internship_id = 100
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

**Step 3 — Add pagination:** Never return all results at once. Use LIMIT/OFFSET or cursor-based (keyset) pagination using the last seen `created_at` value — faster than OFFSET for deep pages.

**Step 4 — In Django ORM:**
```python
Application.objects.filter(internship_id=100) \
    .only('id', 'student_id', 'cover_letter', 'status', 'resume', 'created_at') \
    .order_by('-created_at')[:20]
```

---

**3. What indexes will you create?**

- `(internship_id, created_at DESC)` — primary optimisation, covers both the filter and sort in one index scan.
- `(student_id)` — for the student's own application list view.
- `(student_id, internship_id)` — already exists as `unique_together`, covers duplicate-application checks.
- Partial index on `(internship_id) WHERE status = 'pending'` — if companies frequently filter pending applications specifically, this smaller index is faster.

```python
class Meta:
    indexes = [
        models.Index(
            fields=['internship_id', '-created_at'],
            name='app_internship_created_idx'
        ),
        models.Index(
            fields=['student_id'],
            name='app_student_idx'
        ),
    ]
```

---

**4. How will you measure performance improvement?**

- **EXPLAIN ANALYZE:** Run the query before and after with `EXPLAIN (ANALYZE, BUFFERS)` to compare the execution plan, rows scanned, and time taken.

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, student_id, status, created_at
FROM applications
WHERE internship_id = 100
ORDER BY created_at DESC LIMIT 20;
```

Look for: `Seq Scan` (bad) changing to `Index Scan` or `Index Only Scan` (good). `Rows removed by filter` dropping from millions to near zero.

- **pg_stat_statements / pgBadger:** Monitor slow query logs to catch regressions in production.
- **Load testing:** Use `locust` or `k6` to simulate 50,000 concurrent students and measure p95/p99 latencies before and after the index.
- **Django Silk / Django Debug Toolbar:** Profile ORM queries in development — identify N+1 patterns and duplicated queries.
- **APM tools:** New Relic or Datadog APM traces show end-to-end latency per endpoint, making it clear which DB call is the bottleneck.

---

*End of Answer Sheet — Sections C & D*
