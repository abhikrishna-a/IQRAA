IQRAA Mark Pvt Ltd - Backend Developer Technical Assessment
Sections C & D - Model Answers


SECTION C - Scalability & Problem Solving


Scenario: 1,000 internships go live. Within an hour, 50,000 students start applying.

Q1. How would your system handle this traffic?

A single Django server isnt going to cut it with 50k users hitting us at once. Heres what Id do: Put a load balancer (AWS ALB or Nginx) in front so traffic gets spread across multiple app servers instead of hammering one box. Set up auto-scaling so when CPU or memory spikes, new instances spin up automatically without me having to wake up at 3 AM. Tune gunicorn with workers = (2 x CPU cores) + 1 per server - thats the sweet spot for Django. Offload static assets to a CDN (CloudFront) so Django isnt wasting time serving files it shouldnt be serving. Use PgBouncer for connection pooling - without it, 50k connections would kill PostgreSQL instantly.

Q2. What indexes would you add?

Indexes are cheap to create and make a huge difference. Heres what Id put in place: users(email) - Login looks up by email, without this every login scans the whole user table. Already in place. applications(student, internship) - Covers the duplicate check and its already enforced by unique_together. Already in place. applications(internship_id) - Companies need to see who applied to their posting. Would add. applications(student_id) - Students checking their own application history. Would add. internships(status) - Filtering by open/closed is a common query. Would add. internships(company_id) - Companies viewing their own listings. Would add.

Q3. How would you keep response times under 500ms?

A few things already done and a few Id add. Already in place: select_related() on every FK query so no N+1 problems. Pagination with page and limit params so no endpoint dumps unlimited rows. Would add: Redis cache for the internship listing endpoint. Its the most-read endpoint by far. Cache it for 30-60 seconds. Serving 50k requests from Redis instead of PostgreSQL is night and day. Read replicas so all SELECT queries go to a replica and the primary only handles writes. Django Debug Toolbar during development to catch slow queries before they hit production. Query timeouts so one bad query doesnt hog the connection pool and take everything down with it.

Q4. How would you prevent duplicate applications?

Two layers of protection - belt and suspenders approach. In the view: Before inserting, check if Application.objects.filter(student=user, internship_id=id).exists(). If it exists, return 409 Conflict immediately. This saves a wasted DB insert attempt. In the database: unique_together = (student, internship) on the Application model. This is the real safety net. Even if two requests slip past the pre-check at the exact same millisecond, the database itself will reject the duplicate and throw an IntegrityError, which gets caught and returned as 409. Under real high concurrency, the DB constraint is the only thing you can truly trust. Two concurrent requests can both pass the pre-check before either one commits.

Q5. Would you use Redis?

Absolutely. Right now the project doesnt use Redis, but heres exactly where Id plug it in. Cache layer: Cache internship listings with keys like internships:page:1:limit:10. Invalidate whenever someone creates, updates, or deletes an internship. TTL of 30-60 seconds. Rate limiting: Replace the current in-memory RATE_LIMIT dict with Redis counters. The dict works fine for one server but breaks with multiple workers. Redis works everywhere. Session store: Django session backend pointing to Redis instead of the database. Queue broker: Celery uses Redis as its message broker for background tasks.

Q6. Would you use queue systems (RabbitMQ / Kafka)?

Yes - Celery with Redis as the broker. The API should respond fast and let background workers handle the slow stuff. Confirmation emails: Student applies, API returns 201 instantly, Celery sends the email in the background. Status change notifications: Company updates status, Celery notifies the student. Resume scanning: Upload accepted, queue a background virus scan. If the platform grows and needs event streaming for analytics pipelines or audit trails, Id look at Kafka. But for this scale, Celery with Redis does the job without overcomplicating things.

Q7. How would you scale the system long-term?

App servers: Horizontal scaling all the way. JWT is stateless so any instance handles any request. Containerize with Docker and orchestrate with Kubernetes. Database: Read replicas first. If the data crosses 100 million rows, consider sharding by company_id. File storage: Move media uploads (resumes, profile pics, logos) to S3 with CloudFront. Django shouldnt be serving files. Architecture: Keep it as a monolith until the team grows. Split into microservices for auth, internships, and applications only when the deployment cadence demands it. Monitoring: Prometheus with Grafana for metrics, Sentry for error tracking, structured JSON logs shipped to ELK or CloudWatch.


SECTION D - Query Optimization


The problem query: SELECT * FROM applications WHERE internship_id = 100 ORDER BY created_at DESC;
Table size: Over 10 million rows.

Q1. Why is it slow?

Full table scan: No index on internship_id means PostgreSQL has to read all 10 million rows one by one. No sort index: ORDER BY created_at without an index forces PostgreSQL to do an in-memory sort of the entire result set. SELECT *: Its fetching every single column when maybe you only need 3 or 4 of them. No LIMIT: The database has to return every matching row instead of just a page.

Q2. How would you fix it?

Step 1 - Add a composite index: CREATE INDEX idx_app_internship_created ON applications (internship_id, created_at DESC). This is the big one. A single index that covers both the WHERE filter and the ORDER BY. PostgreSQL can satisfy the entire query just by scanning the index without touching the table at all. Thats called an Index Only Scan.

Step 2 - Only ask for what you need: SELECT id, student_id, status, created_at FROM applications WHERE internship_id = 100 ORDER BY created_at DESC LIMIT 20 OFFSET 0. Less columns means less I/O which means faster response.

Step 3 - Always paginate. Never return all results. For deep pages, use cursor-based pagination using the last created_at value instead of OFFSET. OFFSET gets progressively slower the deeper you go.

Step 4 - In Django ORM: Application.objects.filter(internship_id=100).only('id', 'student_id', 'status', 'created_at').order_by('-created_at')[:20]

Q3. Which indexes specifically?

(internship_id, created_at DESC) - Covers both the WHERE filter and the ORDER BY in one index. This is the primary one. (student_id) - Speeds up the my applications page for students. (student_id, internship_id) - Already exists. Covers the duplicate check. Partial index on (internship_id) WHERE status = 'pending' - If companies frequently filter by pending status, this smaller index is faster than a full index.

Q4. How would you verify the improvement?

EXPLAIN ANALYZE: Run it before and after adding the index. Look for Seq Scan (bad) changing to Index Only Scan (good). The row count should drop from millions to near zero. pg_stat_statements or pgBadger: Track slow query regressions in production. locust or k6: Simulate 50,000 concurrent users and measure p95 and p99 latency before and after adding the index. Django Debug Toolbar or Silk: Profile queries during development to catch problems early. APM tools like New Relic or Datadog: End-to-end traces showing exactly which database call is the bottleneck.

