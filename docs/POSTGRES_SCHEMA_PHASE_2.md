# PostgreSQL Schema Phase 2 Design

## Purpose

This document turns the Phase 0 Mongo inventory into a relational schema direction for PostgreSQL and SQLAlchemy. It is intentionally a design gate before broad ORM model creation.

## Baseline Decisions

- Primary keys use PostgreSQL `uuid` columns with `uuidv7()` server default and are exposed through APIs as strings.
- API contracts remain Pydantic schemas; database rows are SQLAlchemy ORM models.
- SQLAlchemy models use `Mapped[...]` and `mapped_column(...)`.
- Timestamps are timezone-aware UTC.
- Soft delete uses a nullable `deleted_at` timestamp where retention is required; Phase 2 must explicitly classify which tables are soft-deleted and which can be hard-deleted.
- Existing Mongo collections are ported into normalized tables with explicit foreign keys where domain rules allow it.
- Middleware remains DB-free; auth authority continues to come from JWT plus Redis revocation checks.

## Naming Conventions

| Layer | Convention | Example |
| --- | --- | --- |
| Postgres table | plural snake_case | `genres`, `product_option_values`, `business_books` |
| SQLAlchemy ORM class | singular + `Orm` suffix | `GenreOrm`, `ProductOptionValueOrm` |
| FastAPI router prefix | plural kebab-case | `/genres`, `/product-option-values`, `/business-books` |
| Pydantic schema | singular PascalCase | `GenreRead`, `ProductOptionValueCreate`, `VariantUpdate` |
| Repository module | singular domain folder | `app/genre/repository.py`, `app/product_option/repository.py` |

Rules:

- Tables hold many rows, so they are plural.
- Schemas represent one entity shape, so they stay singular.
- Controllers expose plural resource paths to match REST expectations.
- ORM classes stay singular to match the domain object they map.

## Inventory Domain Vocabulary

Rename the configuration-stage entities so **variant** means only the final sellable SKU (price, stock, SKU). The choice-definition tables should not reuse the word "variant."

| Legacy Mongo module / collection | New Postgres table | New domain term | Role |
| --- | --- | --- | --- |
| `variant_type` | `product_options` | product option | Category/dimension of choice (e.g. Format, Condition) |
| `variant_option` | `product_option_values` | product option value | Concrete choice under a product option (e.g. Hardcover, Like New) |
| `variant_config` | `variant_product_option_values` | variant product option value | Links a sellable `variant` to the `product_option_value` rows that define it |
| `variant` | `variants` | variant | Final sellable SKU for a business listing |

API surface after rename:

- `/product-options` — manage product option categories
- `/product-option-values` — manage values within a category
- `/variants` — manage sellable SKUs and their product option values

Schema examples:

- `ProductOptionRead`, `ProductOptionCreate`, `ProductOptionUpdate`
- `ProductOptionValueRead`, `ProductOptionValueCreate`
- `VariantRead`, `VariantCreate` (includes at least one `product_option_value_id`)

## Shared Table Conventions

Most tables should use these shared columns:

| Column | Type | Rule |
| --- | --- | --- |
| `id` | `uuid` | Primary key, `DEFAULT uuidv7()` (PostgreSQL 18+) |
| `status` | `varchar(32)` or enum | Default `ACTIVE`, except lifecycle-specific tables |
| `created_at` | `timestamptz` | Required, server default `now()` |
| `updated_at` | `timestamptz` | Required, server default `now()`, updated on write |
| `deleted_at` | `timestamptz null` | Null means active/not deleted; non-null means soft-deleted |

Use partial indexes for common active-row lookups where useful:

```sql
WHERE deleted_at IS NULL
```

Do not add an implicit global query filter that silently hides deleted rows from every ORM query. Repositories should call explicit helpers such as `not_deleted(Table.deleted_at)` so retention behavior is visible in code and easy to test.

## Delete And Retention Policy

PostgreSQL gives us several deletion patterns:

- **Timestamp soft delete:** keep the row and set `deleted_at`. This is the chosen migration direction because deletion is independent from lifecycle status.
- **Status-based soft delete:** keep the row and set `status = 'DELETED'`. This is the current Mongo behavior, but it should be replaced during the PostgreSQL port.
- **Hard delete:** physically remove the row. Use only for data with no audit, analytics, legal, or relationship value.
- **Archive table:** move older/deleted rows to a historical table. Useful later for very large tables, not needed for the first migration.

Initial classification:

| Category | Initial policy | Reason |
| --- | --- | --- |
| Users, businesses, memberships, roles, privileges | Soft delete | Auth, audit, ownership history |
| Books, authors, genres, business listings, variants | Soft delete | Catalog history, analytics, order references |
| Orders, order items, ratings | Prefer immutable lifecycle statuses plus `deleted_at` only for administrative removal | Audit, finance, customer support |
| Platform invites and password reset tokens | Keep rows with lifecycle/used status, later prune expired rows by retention policy | Security audit and abuse investigation |
| Entity images | Do not migrate as a standalone table initially | Asset URLs now live on related tables; reviews can add image fields/tables when needed |

Hard delete can be introduced later for short-lived operational data after retention requirements are clear.

## Core Identity And Business Tables

### `users`

Source: `app/user/model.py`

Columns:

- `id uuid primary key`
- `role_id uuid null` initially preserved for compatibility, but review whether this belongs to legacy global roles
- `first_name varchar not null`
- `last_name varchar not null`
- `middle_name varchar null`
- `country_code varchar null`
- `phone_number varchar null`
- `email varchar not null`
- `profile_image varchar null`
- `password varchar not null`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Unique lower-cased email. Prefer `citext` or functional unique index on `lower(email)`.
- Index on `status`.

Notes:

- Public response schemas must not include `password`.
- `NEW` status is required for platform bootstrap/password-change flows.

### `businesses`

Source: `app/business/model.py`

Columns:

- `id uuid primary key`
- `user_id uuid not null references users(id)`
- `name varchar not null`
- `description text null`
- `logo varchar null`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Index on `user_id`.
- Unique active business owner on `user_id` for the initial migration.

Notes:

- The product may later allow one user to own multiple businesses/brands. Keep that as a post-migration iteration with explicit guardrails instead of widening the first schema port.

### `business_users`

Source: `app/business_user/model.py`

Columns:

- `id uuid primary key`
- `business_id uuid not null references businesses(id)`
- `user_id uuid not null references users(id)`
- `role_id uuid not null references roles(id)`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Unique active membership on `(business_id, user_id)` where `deleted_at IS NULL`.
- Index on `user_id` for context switching.
- Index on `business_id` for business user management.

## Role And Privilege Tables

### `roles`

Source: `app/role/model.py`

Columns:

- `id uuid primary key`
- `name varchar not null`
- `code varchar not null`
- `description text null`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Unique active role `code`.

Notes:

- Current owner behavior uses a synthetic `"owner-role-id"` and hardcoded privileges. Preserve behavior first, then model owner authority explicitly after auth-critical tests pass.

### `privileges`

Source: `app/privilege/model.py`

Columns:

- `id uuid primary key`
- `code varchar not null`
- `name varchar not null`
- `module_name varchar not null`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Unique active `code`.
- Index on `module_name`.

### `role_privileges`

Source: `app/role_privilege/model.py`

Columns:

- `id uuid primary key`
- `role_id uuid not null references roles(id)`
- `privilege_code varchar not null`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Unique active mapping on `(role_id, privilege_code)` where `deleted_at IS NULL`.
- `privilege_code` should remain the stable authorization authority key.
- Add a foreign key from `role_privileges.privilege_code` to `privileges.code` if `privileges.code` is unique and treated as immutable.

Notes:

- `app/module/query.py` currently writes into `privilege` and `role_privilege`; fix that write shape when this domain is ported.
- The `privileges.id` UUID is still useful as a table primary key, but token materialization and authorization checks should continue to use stable privilege codes such as `READ_ORDER`.

## Platform Tables

### `platform_users`

Source: `app/platform_user/model.py`

Columns:

- `id uuid primary key`
- `user_id uuid not null references users(id)`
- `platform_privilege_set_id uuid not null references platform_privilege_sets(id)`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Unique active `user_id`.
- Index on `platform_privilege_set_id`.

### `platform_invites`

Source: `app/platform_invite/model.py`

Columns:

- `id uuid primary key`
- `email varchar not null`
- `platform_privilege_set_id uuid not null references platform_privilege_sets(id)`
- `token_hash varchar not null`
- `expires_at timestamptz not null`
- `status varchar(32) not null`
- `invited_by uuid not null references users(id)`
- `created_at timestamptz not null`
- `accepted_at timestamptz null`

Constraints/indexes:

- Unique `token_hash`.
- Index on lower-cased `email`.
- Index on `(status, expires_at)`.

Notes:

- Raw invite tokens must never be stored.
- Acceptance should be transactional: create `users`, create `platform_users`, mark invite accepted.

### `platform_privileges`, `platform_privilege_sets`, `platform_privilege_set_privileges`

Source modules:

- `app/platform_privilege`
- `app/platform_privilege_set`
- `app/platform_privilege_set_privilege`

Constraints/indexes:

- Unique active `platform_privileges.code`.
- Unique active `platform_privilege_sets.name`.
- Unique active mapping on `(privilege_set_id, privilege_code)`.

## Catalog Tables

### `books`

Source: `app/book/model.py`

Initial columns should preserve current app behavior:

- `id uuid primary key`
- `title varchar not null`
- `image varchar null`
- `synopsis text null`
- `status varchar(32) not null`
- timestamps

Phase 2 design should leave room for canonical fields from the workspace rules:

- `normalized_title`
- `isbn`
- `language`
- `publication_year`
- `metadata jsonb`

### `authors`

Source: `app/author/model.py`

Initial columns:

- `id uuid primary key`
- `first_name varchar not null`
- `last_name varchar not null`
- `middle_name varchar null`
- `about text null`
- `image varchar null`
- `followers integer not null default 0`
- `status varchar(32) not null`
- timestamps

Phase 2 design should leave room for canonical author fields:

- `canonical_name`
- `normalized_name`
- `bio`
- `metadata jsonb`
- `created_by_business_id uuid null`

### `book_authors`

Columns:

- `id uuid primary key`
- `book_id uuid not null references books(id)`
- `author_id uuid not null references authors(id)`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Unique active pair on `(book_id, author_id)` to prevent the same author being linked to the same book more than once.

Notes:

- This remains many-to-many: one book can have many authors, and one author can belong to many books. The uniqueness rule only prevents duplicate join rows for the same pair.

### `genres` And `book_genres`

Constraints/indexes:

- Unique active `genres.name`.
- Unique active pair on `book_genres(book_id, genre_id)` to prevent duplicate genre links.

Notes:

- This remains many-to-many: one book can have many genres, and one genre can belong to many books.

## Business Listing And Inventory Tables

### `business_books`

Source: `app/business_book/model.py`

Columns:

- `id uuid primary key`
- `book_id uuid not null references books(id)`
- `business_id uuid not null references businesses(id)`
- `synopsis text null`
- `image varchar null`
- `status varchar(32) not null default 'DRAFT'`
- timestamps

Constraints/indexes:

- Index on `(business_id, status)`.
- Unique active listing on `(business_id, book_id)` because a business should not list the same canonical book more than once.

### `variants`

Source: `app/variant/model.py`

Columns:

- `id uuid primary key`
- `business_book_id uuid not null references business_books(id)`
- `description text null`
- `stock integer not null`
- `price numeric(12, 2) not null`
- `currency char(3) not null`
- `discount numeric(5, 2) null`
- `sku varchar null`
- `image varchar null`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Index on `(business_book_id, status)`.
- Optional unique active `sku` per `business_book_id` if SKU uniqueness is a product rule.
- Check `stock >= 0`.
- Check `price >= 0`.
- Check `discount is null or discount between 0 and 100`.

### `product_options`

Source: legacy `app/variant_type`

Represents a category of choice used to build sellable variants (e.g. Format, Condition). Platform-wide inventory vocabulary.

Columns:

- `id uuid primary key`
- `name varchar not null`
- `status varchar(32) not null`
- timestamps
- `deleted_at timestamptz null`

Constraints/indexes:

- Unique active `name` where `deleted_at IS NULL`.

### `product_option_values`

Source: legacy `app/variant_option`

Represents a concrete choice within a product option category (e.g. Hardcover, Like New).

Columns:

- `id uuid primary key`
- `product_option_id uuid not null references product_options(id)`
- `value varchar not null`
- `status varchar(32) not null`
- timestamps
- `deleted_at timestamptz null`

Constraints/indexes:

- Unique active value per product option: `(product_option_id, value)` where `deleted_at IS NULL`.
- Index on `product_option_id`.

### `variant_product_option_values`

Source: legacy `app/variant_config`

Join table expressing which `product_option_value` rows compose a sellable `variant`. Seller-defined inventory structure, not a customer action.

Columns:

- `id uuid primary key`
- `variant_id uuid not null references variants(id)`
- `product_option_value_id uuid not null references product_option_values(id)`
- `status varchar(32) not null`
- timestamps
- `deleted_at timestamptz null`

Constraints/indexes:

- Unique active pair: `(variant_id, product_option_value_id)` where `deleted_at IS NULL`.
- At most one `product_option_value` per `product_option` on a given variant (enforce in service layer or DB constraint over joined `product_option_id`).

Open design item:

- A sellable variant must include at least one `product_option_value`.
- Duplicate product-option-combination checks across variants on the same `business_book` remain application-level for the first port; a generated signature table can come later.

## Orders And Ratings

### `orders`

Source: `app/order/model.py`

Columns:

- `id uuid primary key`
- `user_id uuid not null references users(id)`
- `reference varchar not null`
- `currency char(3) not null`
- `total_amount numeric(12, 2) not null`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Unique `reference`.
- Index on `(user_id, status)`.
- Check `total_amount >= 0`.

### `order_items`

Columns:

- `id uuid primary key`
- `order_id uuid not null references orders(id)`
- `variant_id uuid not null references variants(id)`
- `quantity integer not null`
- `unit_price numeric(12, 2) not null`
- `currency char(3) not null`
- `discount_applied numeric(5, 2) null`
- `status varchar(32) not null`
- timestamps

Constraints/indexes:

- Index on `order_id`.
- Index on `variant_id`.
- Check `quantity > 0`.
- Check `unit_price >= 0`.

### `book_ratings` And `business_ratings`

Constraints/indexes:

- `book_ratings.book_id references books(id)`.
- `book_ratings.user_id references users(id)`.
- `business_ratings.business_id references businesses(id)`.
- `business_ratings.user_id references users(id)`.
- `business_ratings.order_item_id references order_items(id) null`.
- Enforce one rating per eligible purchase/order when the exact service rule is ported.
- Check rating range, likely `1 <= rating <= 5`.

## Entity Images

Source: `app/entity_image/model.py`

Current Mongo shape is polymorphic:

- `entity_name`: `BUSINESS_RATING`, `VARIANT`, `BUSINESS_BOOK`
- `entity_id`: ObjectId of the referenced entity

Recommended Phase 2 decision:

- Do not migrate `entity_images` as a standalone table initially.
- Continue storing asset links directly on related tables where that is already happening, such as `business_books.image`, `variants.image`, `businesses.logo`, and catalog image fields.
- If reviews/ratings need images, add image support directly to the rating/review schema or introduce a typed review image table when that feature is implemented.

Reason:

- The table was an early asset-linking decision and is no longer central to current persistence.
- PostgreSQL cannot enforce a normal FK across multiple target tables with one `entity_id` column.
- Removing it from the first migration reduces polymorphic schema complexity.

## Migration Order

Recommended ORM creation order:

1. `users`
2. `roles`, `privileges`, `role_privileges`
3. `businesses`, `business_users`
4. Platform privilege tables, `platform_users`, `platform_invites`
5. `books`, `authors`, `genres`
6. `book_authors`, `book_genres`
7. `business_books`
8. `product_options`, `product_option_values`
9. `variants`, `variant_product_option_values`
10. `orders`, `order_items`
11. Ratings

This order keeps foreign keys straightforward and matches the planned low-risk to high-risk domain port sequence.

## Phase 3 Proof-Of-Pattern Selection

Use `genre` as the first low-risk domain port.

Reason:

- It is simple CRUD.
- It has no required foreign keys.
- It exercises the target structure: `orm.py`, `schemas.py`, typed `repository.py`, Alembic migration, UUID primary key, lifecycle `status`, and `deleted_at` soft delete.
- It can remain alongside the existing Mongo-backed `model.py`/`query.py` until the route cutover is deliberate.

## Phase 2 Acceptance Criteria

Phase 2 is complete when:

- Table ownership and foreign keys are agreed.
- Soft-delete and timestamp conventions are agreed.
- High-value unique constraints are selected.
- `entity_image` has an explicit decision: do not migrate as a standalone table initially.
- The first Alembic revision can be created from reviewed ORM models.
- At least one low-risk domain is selected for the Phase 3 proof-of-pattern port.

