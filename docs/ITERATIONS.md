# Iterations backlog

Future improvements and deferred decisions. Not blockers for current MVP work.

---

## Business ownership

### Allow one user to own multiple businesses or brands

**Context:** The PostgreSQL migration will initially enforce one active owned business per user for simplicity and to preserve current behavior. The product may later allow one user to own multiple businesses when they represent separate brands.

**Why defer:** Multi-business ownership affects onboarding, context switching, owner recovery, billing, analytics, route defaults, and frontend business selection. It should be designed as a product capability after the database migration is stable.

**Possible guardrails:**

1. Require each owned business to have a distinct normalized brand name per owner.
2. Require explicit business selection after login if the user owns or belongs to more than one active business.
3. Keep one active execution context only; never infer business context from route or cached state.
4. Require each business to have exactly one owner, even if a user owns multiple businesses.
5. Prevent cross-business data reuse: inventory, orders, ratings, staff, and business-scoped cache must remain isolated by `business_id`.
6. Consider verification requirements before allowing multiple live brands for the same owner.
7. Define how billing, deletion, ownership transfer, and owner recovery work per business.

**Eligibility requirements before enabling multi-business ownership:**

1. Require manual platform approval before a user can own multiple active businesses.
2. Require each business to represent a genuinely separate seller profile, brand, or legal entity.
3. Require distinct legal/business registration identifiers where available, such as registration number or tax ID.
4. Require separate verified payout destinations for each business.
5. Require distinct business contact email addresses and phone numbers.
6. Require business profiles, branding, and operating details that do not intentionally mislead customers into thinking unrelated accounts are independent.

**Operational and fraud guardrails:**

1. Track internal account-link signals such as payout destination, verified legal identifiers, device fingerprints where legally permitted, IP patterns, and shared operational metadata.
2. Maintain an internal linked-account health state so platform risk decisions can evaluate related businesses together.
3. Cascade suspensions or restrict linked accounts when fraud, self-dealing, or policy abuse is confirmed on one account.
4. Block linked businesses from buying from, reviewing, or rating each other.
5. Prevent one owner from listing the same canonical book/edition across multiple owned businesses to manipulate price discovery, ranking, or search placement.
6. Flag catalog overlap between linked businesses for review; exact collision rules should depend on the target seller audience.
7. Keep linked-account data platform-only and never expose linkage signals to customers or business staff.

**Platform UX requirements:**

1. Provide a parent-child dashboard where one user identity can switch between approved merchant profiles.
2. Keep token replacement atomic on business switch and preserve the single active business context invariant.
3. Require explicit business selection when multiple businesses are available.
4. Keep business-scoped data, cache, permissions, analytics, and notifications isolated per `business_id`.
5. Support platform review, approval, suspension, and revocation of multi-business privileges.

**Schema direction when enabled:** Replace the initial unique active owner constraint on `businesses.user_id` with constraints that enforce one owner per business and optional uniqueness on `(owner_user_id, normalized_business_name)`.

**Schema/data candidates when enabled:**

- `business_verifications` for legal identifiers, verification status, and review metadata.
- `business_payout_accounts` for verified payout destinations.
- `business_owner_links` or `linked_business_accounts` for internal linkage and risk state.
- `multi_business_applications` for approval workflow and reviewer decisions.
- Catalog collision checks over canonical `book_id`, edition metadata, ISBN, and business ownership links.

**Recommendation:** Keep one active owned business per user for the migration. Revisit after context switching, ownership transfer, and business selection UX are stable.

**Open product question:** Refine catalog collision rules after deciding whether the primary seller audience is independent authors selling their own work or used-book resellers/bookstores.

**Related files:**

- `app/business/model.py`
- `app/business/query.py`
- `app/business/service.py`
- `app/user/service.py` — context switching

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
