# Seed Scripts

Scripts for bootstrapping a fresh PostgreSQL database after `alembic upgrade head`.

## Cutover order (dev/staging)

```bash
# 1. Apply schema
alembic upgrade head

# 2. Reference data (roles, privileges, platform sets, product options)
python scripts/seed_defaults.py

# 3. Platform bootstrap user (set your own credentials)
PRINT_SA_EMAIL=admin@example.com PRINT_SA_PASSWORD=changeme python scripts/seed_super_admin.py

# 4. Optional catalog CSVs
python scripts/upload_seeds.py --all

# 5. Optional smoke-test users + business listings (dev)
python scripts/seed_smoke_test.py
```

**Prerequisites:** PostgreSQL reachable via `POSTGRES_DSN` (see `.env.example`).

After a reset, all new primary keys should be UUIDv7 (version nibble `7` in the standard string form).

## seed_defaults.py

Seeds default records for the application:

1. **Roles** — `OWNER` role (code: `OWNER`)
2. **Privileges** — standard CRUD privileges from `app.auth.privilege_catalog`
3. **Role-privilege mappings** — owner-default privileges mapped to `OWNER`
4. **Platform privileges** — platform admin catalog
5. **Platform privilege sets** — Super Admin, Admin, Moderator
6. **Platform privilege set mappings**
7. **Product options** — Condition and Format variant vocabulary

```bash
python scripts/seed_defaults.py
```

Idempotent: skips rows that already exist.

## seed_super_admin.py

Creates the platform super admin per MDC-PU bootstrap:

- `USER` with status `NEW` (password change on first login)
- `PLATFORM_USER` linked to the Super Admin privilege set

```bash
PRINT_SA_EMAIL=admin@example.com PRINT_SA_PASSWORD=changeme python scripts/seed_super_admin.py
```

**Required:** `PRINT_SA_EMAIL`, `PRINT_SA_PASSWORD`

**Optional:** `PRINT_SA_FNAME` (default: Super), `PRINT_SA_LNAME` (default: Admin)

Run `seed_defaults.py` first.

## upload_seeds.py

Uploads catalog data from CSV via Postgres repositories (genres, authors, books).

```bash
python scripts/upload_seeds.py --type authors --file scripts/seeds/authors.csv
python scripts/upload_seeds.py --type genres --file scripts/seeds/genres.csv
python scripts/upload_seeds.py --type books --file scripts/seeds/books.csv
python scripts/upload_seeds.py --all
```

CSV files live in `scripts/seeds/`. Upload genres before books. Re-running `--all` creates duplicates — use on a fresh DB only.

## seed_smoke_test.py

Creates dev smoke-test accounts and a marketplace slice:

1. **Seller** — customer user with an owned business, ACTIVE business-book listings, and catalog variants
2. **Five extra sellers** — Harbor Lane Books, Folio & Co., Pagecraft Collective, Northstar Rare & New, Inkwell Market (each with multiple book listings and variants)
3. **Customer** — plain customer user (no business)

```bash
python scripts/seed_smoke_test.py
```

**Optional:** `PRINT_ST_SELLER_EMAIL`, `PRINT_ST_SELLER_PASSWORD`, `PRINT_ST_CUSTOMER_EMAIL`, `PRINT_ST_CUSTOMER_PASSWORD`, `PRINT_ST_BUSINESS_NAME`

Defaults: `seller@example.com` / `customer@example.com` with password `changeme`.

Run after `seed_defaults.py` and `upload_seeds.py --all`. Idempotent: skips existing users, business, listings, and variants.
