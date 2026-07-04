# Print API

FastAPI backend for **Print**, a marketplace platform for pre-owned books. Sellers manage inventory and orders in a business context; customers browse and purchase in a customer context; platform operators administer the system through a separate admin surface.

Companion web app: [print-web](https://github.com/) (Next.js).

## Features

- **Multi-context auth** — JWT access tokens for `CUSTOMER`, `BUSINESS`, and `PLATFORM` contexts with explicit context switching
- **Privilege-based authorization** — materialized privileges in tokens; fail-closed middleware with no DB lookups in auth layer
- **Global catalog** — canonical books and authors with provisional creation for fast seller onboarding
- **Business operations** — inventory, orders, ratings, roles, and business-scoped listings
- **Platform admin** — invite-only platform users, privilege sets, and moderation workflows
- **Media uploads** — S3 presigned URLs for staged book cover uploads

## Stack

- Python 3.13+
- [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- MongoDB (Motor async driver)
- Redis (token revocation)
- AWS S3 (image storage) with CloudFront CDN for public reads
- PyJWT

## Project layout

```
app/
  main.py              # FastAPI app entrypoint
  middleware/          # Auth and request timing
  utility/             # Config, database, redis, tokens, authorization
  author/ book/ ...    # Domain modules (controller / service / query / model)
scripts/               # Database seed utilities
```

See [AUTHORIZATION.md](./AUTHORIZATION.md) for the privilege and context model.

## Getting started

### Prerequisites

- Python 3.13+
- MongoDB (local or Atlas)
- Redis (local or Redis Cloud)
- AWS credentials with S3 access (for image uploads)

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure

Copy the example env file and fill in values:

```bash
cp .env.example .env
```

| Variable | Description |
| --- | --- |
| `APP_ENV` | `development` or `production` |
| `JWT_SECRET` | Signing key — must match `print-web` |
| `MONGODB_URI` | Mongo connection string (`mongodb+srv://` enables TLS) |
| `MONGODB_DB_NAME` | Database name (default: `print`) |
| `REDIS_HOST` | Redis hostname |
| `REDIS_PORT` | Redis port |
| `REDIS_PASSWORD` | Redis password (if required) |
| `REDIS_SSL` | `true` for TLS endpoints (e.g. Redis Cloud) |
| `ASSETS_CDN_URL` | CDN base URL for public images (e.g. CloudFront distribution) |

In production, `JWT_SECRET` is required when `APP_ENV=production`.

Never commit `.env` — it is listed in `.gitignore`.

### Run

```bash
uvicorn app.main:app --reload --port 8000
```

- Client API docs: http://localhost:8000/docs
- Platform admin docs: http://localhost:8000/platform-docs

### Seed data

```bash
# Default roles, privileges, and platform privilege sets
python scripts/seed_defaults.py

# Bootstrap super admin (after seed_defaults)
SUPER_ADMIN_EMAIL=admin@example.com SUPER_ADMIN_PASSWORD=changeme \
  python scripts/seed_super_admin.py

# Optional CSV seed data
python scripts/upload_seeds.py --all
```

See [scripts/README.md](./scripts/README.md) for details.

## API overview

| Area | Examples |
| --- | --- |
| Auth | `/user/login`, `/user/signup`, `/auth/context/business/{id}` |
| Catalog | `/book/read`, `/author/read`, `/variants/read` |
| Business | `/business-books/{id}/variants`, `/business/{id}/orders` |
| Platform | `/platform-user/login`, `/admin/*` (platform context) |

Protected routes require a `Bearer` JWT. Context and privileges are enforced server-side from token claims only.

## Development

```bash
# Run from project root so `app` resolves as a package
uvicorn app.main:app --reload
```

CORS is configured for `http://localhost:3000` and `http://localhost:3001` (print-web).

## Security notes

- Secrets load from environment via `app/utility/config.py` — do not hardcode credentials in source
- Rotate any credentials that were previously committed or shared
- AWS access uses the default credential chain (env vars, `~/.aws/credentials`, or instance role)

## License

Proprietary — all rights reserved.
