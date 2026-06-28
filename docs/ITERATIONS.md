# Iterations backlog

Future improvements and deferred decisions. Not blockers for current MVP work.

---

## Platform invites

### Optimize `mark_expired_query` usage

**Context:** `mark_expired_query()` runs a collection-wide MongoDB `update_many` on every call:

```python
collection.update_many(
    {"status": "PENDING", "expires_at": {"$lt": now}},
    {"$set": {"status": "EXPIRED", "updated_at": now}},
)
```

It is invoked from:

- `create_invite_service` (before duplicate-email check)
- `_require_pending_invite` (resend / revoke)
- `validate_invite_service` (public accept / reject flow)

**Why it exists:** Keeps `status` in sync with `expires_at` so admin lists and duplicate-email checks do not treat overdue rows as still pending.

**Cost:** One extra DB round-trip per invite operation. Negligible at admin invite volume (tens/hundreds of rows). Becomes wasteful if `validate` is hit frequently or the collection grows large.

**Correctness without global sweep:** Single-invite paths already expire lazily:

- `_require_pending_invite` — checks `expires_at` and marks that document `EXPIRED`
- `validate_invite_service` — same for the token being validated

The global pass is housekeeping, not required for accept/reject/resend correctness on one invite.

**Options when optimizing:**

1. **Query-time filter (simplest)** — Treat expiry in reads instead of bulk updates:
   ```python
   {"status": "PENDING", "expires_at": {"$gte": now}}
   ```
   Use in `read_pending_by_email_query` and admin list queries. Remove `mark_expired_query` from create / resend / revoke.

2. **Per-invite only** — Keep expiry logic only where a specific invite is touched. Lists may show `PENDING` until something acts on that row.

3. **Background job** — Cron or scheduler runs `mark_expired_query` every N minutes. Data stays tidy without per-request cost.

4. **Index (if keeping bulk update)** — Compound index on `(status, expires_at)`.

**Recommendation:** Keep as-is for MVP. Revisit if invite volume or public validate traffic increases.

**Related files:**

- `app/platform_invite/query.py` — `mark_expired_query`
- `app/platform_invite/service.py` — call sites
