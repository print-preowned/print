# PostgreSQL Migration Phase 0 Inventory

## Decision Baseline

- Migration target: PostgreSQL **18+** with async SQLAlchemy ORM and Alembic (dev baseline: 18.4).
- Primary keys: PostgreSQL `uuid` columns with **`uuidv7()`** `server_default` (PG 18+), exposed through the API as strings. IDs are assigned on insert; repositories must `flush()` before reading `row.id`. Use a Python UUID library only if app-side generation is needed later.
- Data state assumption: current Mongo data is dev/staging data, so the migration can favor simple re-seeding or repeatable backfills over zero-downtime production cutover machinery.
- Migration style: phased port with a final cutover, not a single big-bang rewrite.
- Authorization invariant: middleware remains DB-free; JWT and Redis continue to be the request authority.
- Typing policy: static checking via Pyright; runtime validation via Pydantic at API boundaries; SQLAlchemy `Mapped[...]` for persistence.
- Naming policy: plural Postgres tables and controller routes; singular Pydantic schemas; see `docs/POSTGRES_SCHEMA_PHASE_2.md` for inventory vocabulary (`product_option`, `product_option_value`, `variant`).

## Current Persistence Shape

The backend currently uses MongoDB through Motor. The only shared database factory is `app/utility/database.py`, but every `query.py` imports it and creates module-level collection handles at import time:

```python
db = get_database()
collection = db["collection_name"]
```

This means the application has no request-scoped database session, unit of work, SQL transaction boundary, or startup/shutdown lifecycle for persistence. The SQLAlchemy migration must introduce those concepts before domain ports begin.

The app follows a consistent pattern:

- `model.py`: Pydantic request/response/entity models.
- `query.py`: direct Mongo access through Motor.
- `service.py`: business rules and response shaping.
- `controller.py`: FastAPI routes and authorization dependencies.

## Structural Improvements By Phase

These are part of the migration direction, not separate cleanup work. Each improvement should land in the phase where it reduces migration risk most.

### Phase 0: Contract And Scope Decisions

- Keep UUID-as-string as the external ID format.
- Confirm that no production-grade zero-downtime migration path is required yet.
- Decide that SQLAlchemy ORM models and Pydantic API schemas should become separate layers instead of continuing the current Mongo-shaped model contract.
- Adopt type policies: Pyright for static checking, `Mapped[...]` for ORM, Pydantic schemas for API I/O.
- Explicitly include the staged `app/customer` module in migration planning, even if it remains deferred from router registration.

### Phase 1: SQL Foundation

- Add a request-scoped `AsyncSession` dependency and engine lifecycle instead of module-level global database handles.
- Introduce shared SQLAlchemy base conventions: UUID primary keys, timezone-aware timestamps, naming conventions, and status/soft-delete mixins.
- Add Alembic from the start so every schema change is explicit and repeatable.
- Keep existing Mongo query modules untouched until the foundation pattern is reviewed.

### Phase 2: Schema Design

- Convert app-enforced relationships into foreign keys where the domain allows it.
- Convert high-value uniqueness rules into database constraints or partial unique indexes.
- Design a consistent `deleted_at` soft-delete strategy so repositories do not hand-code deletion filters in every query.
- Make a deliberate decision for `entity_image`: either preserve the polymorphic `entity_name`/`entity_id` shape temporarily or split it into safer typed associations.
- Normalize timestamps to timezone-aware UTC.

### Phase 3: Low-Risk Domain Ports

- Port simple catalog/admin domains first to establish the repository pattern.
- Replace `query.py` global collections with repository functions that accept an `AsyncSession`.
- Keep controller and service response contracts stable while swapping persistence underneath.
- Fix low-risk discovered issues in the domain being ported, such as the `app/module/query.py` privilege and role-privilege write shape, when that domain is migrated.

### Phase 4: Auth-Critical Domain Ports

- Port `user`, `business`, `business_user`, `role`, `role_privilege`, `platform_user`, and platform privilege mappings.
- Preserve the invariant that middleware does not query the database.
- Replace the hardcoded owner privilege list and synthetic `"owner-role-id"` only if the new schema has a reviewed owner authority model ready; otherwise preserve behavior first and schedule the cleanup immediately after.
- Characterize login and context-switch behavior before and after porting.

### Phase 5: Marketplace Domain Ports

- Replace application-side joins with explicit SQL joins, relationship loading, or focused read models.
- Use real transactions for multi-write flows such as variant creation, variant config creation, soft-delete cascades, invite acceptance, and order writes.
- Add constraints for rating uniqueness and product option combination uniqueness where feasible.
- Preserve public catalog and pagination response shapes.

### Phase 6: Data Migration And Cutover

- Prefer re-seeding reference data and scripted backfills because current data is assumed to be dev/staging.
- Validate counts, required relationships, and critical API flows before switching runtime persistence.
- Remove Motor, `bson`, Mongo config, Mongo-shaped helpers, and `PyObjectId` only after all active modules have moved to SQLAlchemy.

## Type Policies

Python typing is optional at runtime. This project enforces it through static analysis, typed ORM models, and Pydantic validation at API boundaries.

### Layer Responsibilities

| Layer | Tool | Purpose |
| --- | --- | --- |
| Persistence | SQLAlchemy 2.x ORM with `Mapped[...]` | Database rows, relationships, constraints |
| API I/O | Pydantic v2 schemas | Request validation, response serialization, OpenAPI |
| Data access | Typed repository functions | Queries accepting `AsyncSession`, returning ORM rows or domain types |
| Services | Typed functions with explicit return types | Business rules, orchestration, mapping ORM → Pydantic |

Target module layout per domain:

```text
app/user/
  orm.py          # SQLAlchemy User table
  schemas.py      # UserCreate, UserRead, UserUpdate
  repository.py   # async queries with AsyncSession
  service.py
  controller.py
```

Do not use one Pydantic model as both the DB entity and the API contract. The current `model.py` + `PyObjectId` + `_id` alias pattern is a Mongo artifact and will be retired during migration.

### SQLAlchemy ORM Typing

Use SQLAlchemy 2.x typed declarative style, not untyped `Column(...)`:

```python
# Preferred
class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("uuidv7()"),
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)

# Avoid for new code
class User(Base):
    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True)
```

`Mapped[T]` tells both SQLAlchemy and the type checker what attribute types instances expose at runtime.

### Pydantic Schema Typing

Use normal Python types in schemas:

- `uuid.UUID` for IDs (serialized as strings in JSON automatically).
- `datetime` with timezone awareness for timestamps.
- `EmailStr`, `Decimal`, `Literal`, and enums where appropriate.
- `model_config = ConfigDict(from_attributes=True)` on read schemas that map from ORM rows.

Avoid in new schemas:

- `PyObjectId`, `bson.ObjectId`, and `Field(alias="_id")`.
- `Any` unless there is a documented reason.
- Mixing persistence fields (e.g. `password` hash) into public response schemas.

### Static Type Checking (Pyright)

Add Pyright as the project type checker (aligns with Cursor/Pylance).

Start with `typeCheckingMode: "basic"` repo-wide. Tighten to `"strict"` for newly migrated SQLAlchemy modules as they land.

Example `pyrightconfig.json`:

```json
{
  "typeCheckingMode": "basic",
  "include": ["app", "scripts"],
  "exclude": ["**/__pycache__"],
  "reportMissingTypeStubs": "warning",
  "reportUnknownMemberType": "warning",
  "reportUnknownVariableType": "warning",
  "reportUnknownArgumentType": "warning"
}
```

Enforcement rules:

- All new and ported modules must pass `pyright` before merge.
- Legacy Mongo modules are exempt until ported, then must pass on port completion.
- Service and repository functions require explicit parameter and return types.
- Avoid bare `dict` and bare `list` in public function signatures; use `dict[str, T]`, `list[T]`, or typed models.

### Runtime Validation

Static typing catches developer mistakes at edit/CI time. Pydantic catches invalid external input at request time. Both are required:

- Controllers accept Pydantic request schemas as body/path/query parameters.
- Services map validated input to repository calls.
- Controllers return Pydantic response schemas, not raw ORM instances or dicts.

### IDE Support

For better hover and autocomplete:

- Select the correct Python interpreter/venv where project dependencies are installed.
- Enable `python.analysis.typeCheckingMode: "basic"` (or `"strict"`) in editor settings.
- Prefer explicit Pydantic schema classes over dynamic `BaseModel` behavior and custom core-schema types like `PyObjectId`.

Hover will not always expand full Pydantic model shapes; that is a language-server limitation. Explicit typed schemas improve it significantly.

### Type Policies By Phase

**Phase 0**

- Adopt the layer separation policy (ORM / schemas / repository).
- Decide Pyright as the static checker.

**Phase 1**

- Add `pyright` dev dependency and `pyrightconfig.json`.
- Add a CI step: `pyright` must pass for included paths.
- Define shared typed base ORM mixins and Pydantic response wrappers.

**Phase 2**

- All new ORM models use `Mapped[...]` and typed relationships.
- All new Pydantic schemas use standard Python types, not Mongo types.

**Phase 3 onward**

- Each ported domain must ship with `orm.py`, `schemas.py`, and typed `repository.py`.
- Ported domain must pass Pyright before the Mongo `query.py` for that domain is removed.
- No new `Any`, `PyObjectId`, or untyped `Column` in ported code.

**Phase 6**

- Remove `PyObjectId`, `BaseAppModel` ObjectId serializers, and Mongo `json_encoders`.
- Expand Pyright to `strict` repo-wide once legacy Mongo modules are gone.

## Shared Contract Blockers

`app/utility/model.py` is the central Mongo contract:

- `BaseAppModel` serializes `ObjectId` values as strings.
- `PyObjectId` validates strings by coercing them to `bson.ObjectId`.
- Entity models commonly declare `id: PyObjectId = Field(alias="_id", serialization_alias="id")`.

The `_id` to `id` serialization shape can stay stable externally, but `PyObjectId` will reject UUID strings. This must be replaced with a UUID-compatible ID type or removed from public request/response models during the SQLAlchemy port.

Path parameters are already generally typed as `str`, so route signatures should not be the breaking point. The breaking point is ID value format: Mongo `ObjectId` strings are 24 hex characters; UUID strings are 36 characters. The frontend and tests should be checked for ID regexes, length assumptions, or ObjectId-specific validation.

## Collections And Relational Candidates

| Mongo collection | Current module | Relational role | Key references |
| --- | --- | --- | --- |
| `user` | `app/user` | Global identity | `role_id` legacy/user role reference |
| `business` | `app/business` | Business account | `user_id` owner |
| `business_user` | `app/business_user` | Business membership | `business_id`, `user_id`, `role_id` |
| `role` | `app/role` | Business role | none |
| `role_privilege` | `app/role_privilege` | Role privilege mapping | `role_id`, `privilege_code` |
| `privilege` | `app/privilege` | Business privilege catalog | `module_name` logical grouping |
| `platform_user` | `app/platform_user` | Platform access row | `user_id`, `platform_privilege_set_id` |
| `platform_invite` | `app/platform_invite` | Platform invitation | `platform_privilege_set_id`, `invited_by` |
| `platform_privilege` | `app/platform_privilege` | Platform privilege catalog | none |
| `platform_privilege_set` | `app/platform_privilege_set` | Platform privilege set | none |
| `platform_privilege_set_privilege` | `app/platform_privilege_set_privilege` | Platform privilege mapping | `privilege_set_id`, `privilege_code` |
| `password_reset_token` | `app/password_reset_token` | Password reset token | `user_id` |
| `book` | `app/book` | Global book/work | none |
| `author` | `app/author` | Global author/person | none |
| `book_author` | `app/book_author` | Book-author join | `book_id`, `author_id` |
| `genre` | `app/genre` | Genre catalog | none |
| `book_genre` | `app/book_genre` | Book-genre join | `book_id`, `genre_id` |
| `business_book` | `app/business_book` | Business listing | `book_id`, `business_id` |
| `variant` | `app/variant` | Sellable SKU | `business_book_id` |
| `variant_type` → `product_options` | `app/variant_type` | Product option category | none |
| `variant_option` → `product_option_values` | `app/variant_option` | Product option value | `product_option_id` (was `variant_type_id`) |
| `variant_config` → `variant_product_option_values` | `app/variant_config` | Variant ↔ product option value join | `variant_id`, `product_option_value_id` |
| `order` | `app/order` | Customer order | `user_id` |
| `order_item` | `app/order_item` | Order line item | `order_id`, `variant_id` |
| `book_rating` | `app/book_rating` | Book rating | `book_id`, `user_id` |
| `business_rating` | `app/business_rating` | Business/order rating | `business_id`, `user_id`, `order_item_id` |
| `entity_image` | `app/entity_image` | Polymorphic image association | `entity_name`, `entity_id` |

`app/module/query.py` does not have its own collection. It writes to `privilege` and `role_privilege`, which should be revisited during schema design.

## Soft Delete And Status Contract

The current app uses soft deletes almost everywhere:

- Delete operations set `status = "DELETED"`.
- Current Mongo read operations generally filter with `status != "DELETED"`; PostgreSQL repositories should instead filter with `deleted_at IS NULL`.
- There are no hard deletes in normal app query modules.

PostgreSQL should preserve the externally visible behavior while changing the storage mechanism: deletion should become `deleted_at IS NOT NULL`, while `status` should describe lifecycle states such as `ACTIVE`, `DRAFT`, `PENDING`, or `SUSPENDED`. Later, high-value paths can add partial indexes such as `WHERE deleted_at IS NULL`.

Important status variants:

- Most entities default to `ACTIVE`.
- `business_book` uses listing states such as `DRAFT`, `ACTIVE`, `INACTIVE`, and `SUSPENDED`; deletion should move to `deleted_at`.
- `user` can be `NEW`, especially for platform bootstrap/password-change flows.
- `platform_invite` uses invitation lifecycle states like `PENDING`, `ACCEPTED`, `REJECTED`, and `EXPIRED`.
- `password_reset_token` uses `used` and `used_at` rather than a status column.

## High-Risk Query Patterns

### Import-Time Collections

Every query module currently binds Motor collections globally. SQLAlchemy should instead use an `AsyncSession` injected through FastAPI dependencies and passed through service/query or repository functions.

### Application-Side Joins

Mongo relationships are manually stitched in Python with `$in` queries. These should become SQL joins, relationship loading, or explicit repository queries.

Hotspots:

- `app/variant/query.py`: public catalog, config resolution, variant summary.
- `app/business_book/query.py`: business listings with book and variant summaries.
- `app/book_author/query.py`: book-author population.

### Aggregations

`app/variant/query.py` uses aggregation for variant summaries. This maps cleanly to SQL `GROUP BY`, but the behavior should be covered by tests before porting.

### Multi-Write Flows

Some flows write several collections without transaction support today. PostgreSQL should make these atomic.

Examples:

- Variant creation inserts a `variant` and multiple `variant_product_option_values` rows (legacy: `variant_config`).
- Variant soft delete cascades to `variant_product_option_values` (legacy: `variant_config`).
- Business book delete cascades into variants and variant configs.
- Platform invite acceptance creates identity/platform records and marks the invite accepted.

### App-Enforced Uniqueness

Uniqueness is mostly enforced in application code, not indexes. Schema design should convert these into database constraints where possible.

Candidates:

- `user.email`
- `business_user` membership uniqueness per `business_id` and `user_id`
- `role.code`
- `privilege.code`
- `platform_privilege.code`
- `platform_privilege_set.name`
- `platform_invite.token_hash`
- one rating per eligible target/order where required
- variant product option combination uniqueness per `business_book`

## Auth And Context-Switch Impact

The middleware in `app/middleware/auth.py` and token validation in `app/utility/authorization.py` are DB-free and should remain that way.

The DB-dependent auth flows are in `app/user/service.py`:

- Login reads user records and business membership/platform privileges.
- Context switching reads `user`, `business`, `business_user`, `role`, and `role_privilege`.
- Token materialization must still come only from persisted authority and must not infer context from routes or client state.

These flows should receive characterization tests before migration because they enforce the core context model.

## API Compatibility Checklist

Before porting code, verify:

- API responses continue to expose `id` as a string.
- Request bodies that include IDs accept UUID strings.
- Path params remain string-based.
- Frontend code does not assume ObjectId length or regex format.
- Pagination response shape remains unchanged.
- Soft-deleted rows remain hidden by default.
- Token payload shape remains unchanged.
- Public catalog response shape remains unchanged.

## Recommended Phase 0 Test Coverage

Add characterization tests before changing persistence:

- Customer signup and login.
- Platform login for a platform user.
- Customer to business context switch.
- Business to customer context switch.
- Public catalog listing with variant config and effective price.
- Business inventory create/list/delete flow.
- Business book delete cascading to variants/configs.
- Order creation and order item linkage.
- Rating creation rules if the flow is currently implemented.
- Platform invite validate/accept/reject lifecycle.

## Phase 0 Acceptance Criteria

Phase 0 is complete when:

- Current Mongo collections and references are documented.
- UUID-as-string is confirmed as the new external ID format.
- High-risk query flows are identified.
- Auth/context-switch persistence dependencies are identified.
- API compatibility risks are listed.
- Characterization test targets are agreed before any SQLAlchemy rewrite.
- Type policies are documented: layer separation, Pyright enforcement, `Mapped[...]` ORM style, Pydantic schema rules.
- The first implementation milestone is scoped to SQL foundation only: dependencies, settings, engine/session lifecycle, Alembic bootstrap, base ORM conventions, Pyright config, and one low-risk domain proof of pattern.

## Open Follow-Up For Phase 1

Phase 1 should start by adding the SQL foundation without removing Mongo code:

- Add PostgreSQL settings.
- Add async SQLAlchemy engine/session lifecycle.
- Add Alembic.
- Add Pyright dev dependency, `pyrightconfig.json`, and CI enforcement.
- Define shared ORM base conventions with `Mapped[...]` and Pydantic schemas with `from_attributes=True`.
- Pick one low-risk CRUD domain as the proof-of-pattern port.
