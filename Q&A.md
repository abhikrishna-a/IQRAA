# IQRAA Mark Pvt Ltd — Backend Developer Technical Assessment
## Sections C & D — Model Answers

---

## SECTION C — Scalability & Problem Solving (20 Marks)

**Scenario:** 1,000 internships published. Within 1 hour, 50,000 students apply.

---

### 1. How will your system handle this traffic?

- Deploy Django behind a **load balancer** (AWS ALB / Nginx) to distribute requests across multiple app servers
- Use **auto-scaling groups** to spin up new instances when CPU/memory thresholds are crossed
- Configure **gunicorn** with `workers = (2 × CPU cores) + 1` per instance
- Put a **CDN** (CloudFront) in front of static assets to offload the origin server
- Use **PgBouncer** for database connection pooling so the DB isn't overwhelmed

---

### 2. What indexes will you create?

These indexes speed up the most common high-load queries:

| Index | Purpose | Status in project |
|---|---|---|
| `applications(student_id, internship_id)` | Covers duplicate-check lookups | ✅ Already enforced via `unique_together` |
| `applications(internship_id)` | Companies fetching applications for an internship | ❌ Would add |
| `applications(student_id)` | Students listing their own applications | ❌ Would add |
| `internships(status)` | Filtering open/closed listings | ❌ Would add |
| `internships(company_id)` | Company-scoped internship queries | ❌ Would add |
| `users(email)` | Fast login lookups | ✅ Already added |

---

### 3. How will you keep response time below 500ms?

- Use `select_related()` / `prefetch_related()` on all FK/M2M views to **eliminate N+1 queries** (already done)
- **Cache** the internship listing (most-read endpoint) in **Redis** with a 30–60 second TTL — no need to hit the DB 50,000 times/hour
- Use **database read replicas** — route SELECTs to replicas, primary only handles writes
- **Paginate** all list endpoints (already done — `page` + `limit` params)
- Use **Django Debug Toolbar** in development to profile slow queries before they reach production
- Set **database query timeouts** to prevent long-running queries from blocking the connection pool

---

### 4. How will you prevent duplicate applications?

Two layers of defense (already implemented):

1. **Database constraint** — `unique_together = ('student', 'internship')` on the Application model. The DB enforces uniqueness even under race conditions.
2. **Application-level pre-check** — The view runs `Application.objects.filter(student=user, internship_id=id).exists()` before inserting, returning `409 Conflict` early.

Under high concurrency, the DB constraint is the final safety net. If two requests pass the pre-check simultaneously, the second insert hits `IntegrityError`, which is caught and returned as `409`.

---

### 5. Will you use Redis? How?

Yes. Currently not implemented; would add Redis for:

| Role | What it would do |
|---|---|
| **Cache Layer** | Cache paginated internship listings. Key: `internships:page:{n}:limit:{l}`. TTL: 30–60s. Invalidate on create/update/delete |
| **Rate Limiting** | Replace the current in-memory `RATE_LIMIT` dict (per-process, resets on restart) with Redis-backed counters — works across all server instances |
| **Session Store** | Use Redis as the Django session backend |
| **Queue Broker** | Use Redis as the Celery message broker for background tasks |

---

### 6. Will you use Queue Systems (RabbitMQ / Kafka)?

Yes — **Celery with Redis** (or RabbitMQ) as the broker. The API responds immediately, and background tasks handle the rest:

- **Confirmation email** — sent after a student applies (API returns 201 right away)
- **Status change notification** — notify the student via email/push when a company accepts/rejects
- **Resume virus scan** — upload accepted, scan queued in background

Kafka would be considered if the platform later needs event streaming (analytics, audit logs). For this scale, Celery + Redis is sufficient.

---

### 7. How will you scale the system?

| Layer | Strategy |
|---|---|
| **Application** | Horizontal scaling — stateless JWT auth means any instance handles any request. Docker + Kubernetes for orchestration |
| **Database** | Read replicas for SELECT workloads. Shard by `company_id` if data grows beyond 100M+ rows |
| **Media** | Serve resumes/images from S3 + CloudFront, not through Django |
| **Architecture** | Split into microservices (auth, internships, applications) if team size requires it |
| **Monitoring** | Prometheus + Grafana for metrics, Sentry for errors, structured JSON logs to ELK/CloudWatch |

---

## SECTION D — Query Optimization (10 Marks)

**Given query:**
```
SELECT * FROM applications WHERE internship_id = 100 ORDER BY created_at DESC;
```
**Table size:** 10 million+ records

---

### 1. Why is the query slow?

| Problem | Explanation |
|---|---|
| **Full table scan** | No index on `internship_id` — PostgreSQL reads all 10M+ rows |
| **No index on ORDER BY** | Sorting 10M rows by `created_at` requires an expensive filesort (O(n log n)) |
| **SELECT \*** | Fetches all columns — more I/O and network overhead |
| **No LIMIT** | The DB must return every matching row instead of a page |

---

### 2. How do you optimize it?

**Step 1 — Add a composite index:**
```sql
CREATE INDEX idx_app_internship_created ON applications (internship_id, created_at DESC);
```
This covers both the `WHERE` filter and the `ORDER BY` sort in a single index scan.

**Step 2 — Select only the columns you need:**
```sql
SELECT id, student_id, cover_letter, status, resume, created_at
FROM applications
WHERE internship_id = 100
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

**Step 3 — Paginate everything.** Never return all results at once. For deep pages, use cursor-based pagination (keyset pagination using the last `created_at` value) instead of `OFFSET`, which gets slower on deep pages.

**Step 4 — In Django ORM:**
```python
Application.objects.filter(internship_id=100) \
    .only('id', 'student_id', 'cover_letter', 'status', 'resume', 'created_at') \
    .order_by('-created_at')[:20]
```

---

### 3. What indexes will you create?

| Index | Purpose |
|---|---|
| `(internship_id, created_at DESC)` | Primary — covers WHERE filter + ORDER BY in one index |
| `(student_id)` | Speeds up student's own application list view |
| `(student_id, internship_id)` | Already exists as `unique_together`, covers duplicate checks |
| Partial: `(internship_id) WHERE status = 'pending'` | Smaller, faster index if companies frequently filter pending apps |

---

### 4. How will you measure performance improvement?

| Tool | What to look for |
|---|---|
| **EXPLAIN ANALYZE** | Before: `Seq Scan` (scans all rows). After: `Index Only Scan` (scans just the index). Rows scanned drops from millions to near zero |
| **pg_stat_statements / pgBadger** | Monitor slow query logs in production for regressions |
| **locust / k6** | Load test with 50,000 concurrent users, measure p95/p99 latency before and after the index |
| **Django Silk / Debug Toolbar** | Profile ORM queries in development — catch N+1 patterns early |
| **APM tools (New Relic / Datadog)** | End-to-end latency traces showing exactly which DB call is the bottleneck |

---

*End of Answer Sheet — Sections C & D*
