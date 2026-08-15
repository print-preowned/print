# Paystack Escrow Payment Flow

> **Superseded (15 Aug 2026):** Paystack manual subaccount settlement has no public release API. See [`FLUTTERWAVE_ESCROW_PHASE_0.md`](FLUTTERWAVE_ESCROW_PHASE_0.md) and the updated implementation plan. Retained for historical reference only.


Confirm Paystack APIs and operational constraints for:

1. Subaccount split payments with **manual settlement** (escrow-like hold)
2. Escrow **release** mechanism after fulfillment + dispute window
3. **Refund** behaviour on split transactions
4. **Webhooks**, amounts, and integration prerequisites for Phase 1

---

## Decision baseline (confirmed)

| Topic | Conclusion |
| ----- | ---------- |
| Escrow model | **Subaccount split + manual settlement** — aligns with plan update and expert review ([`paystack-escrow-plan-review.html`](paystack-escrow-plan-review.html)) |
| Platform hold + Transfers | **Rejected** — T+1 drains platform balance; regulatory exposure holding third-party funds |
| Order ↔ payment | **Loosely coupled** — `POST /orders` retained; `POST /orders/{id}/payments` initiates Paystack |
| Amounts | **Kobo** (integer minor units) on all Paystack API calls |
| Webhook signing | **Secret key** HMAC-SHA512 of raw body (`x-paystack-signature`); no `PAYSTACK_WEBHOOK_SECRET` env var |

---

## Confirmed API surface (Phase 1 ready)

### 1. Create seller subaccount

```
POST https://api.paystack.co/subaccount
Authorization: Bearer {SECRET_KEY}
Content-Type: application/json
```

**Body (MVP):**

```json
{
  "business_name": "Seller Name",
  "settlement_bank": "058",
  "account_number": "0123456789",
  "percentage_charge": 95,
  "settlement_schedule": "manual",
  "description": "Print seller subaccount",
  "primary_contact_email": "seller@example.com"
}
```

**Notes:**

- `settlement_schedule: "manual"` — Paystack holds the subaccount's share until settlement is triggered ([Subaccount API](https://paystack.com/docs/api/subaccount/)).
- `percentage_charge` — share allocated to the **subaccount** (seller); remainder goes to the **main/integration account** (platform). For a 5% platform fee, set `percentage_charge` to **95** (seller gets 95%).
- Alternative: keep subaccount percentage fixed and pass **`transaction_charge`** (flat kobo to main account) on each `transaction/initialize` for precise per-order fees.
- Response includes `subaccount_code` (`ACCT_...`) → store as `business_subaccounts.provider_subaccount_code`.
- Validate bank details first: `GET /bank/resolve?account_number=...&bank_code=...`.

**Update subaccount:**

```
PUT https://api.paystack.co/subaccount/{id_or_code}
{ "settlement_schedule": "manual", ... }
```

### 2. Initialize split payment

```
POST https://api.paystack.co/transaction/initialize
```

**Body (MVP — single seller subaccount):**

```json
{
  "email": "customer@example.com",
  "amount": "1000000",
  "reference": "PAY-abc123",
  "currency": "NGN",
  "subaccount": "ACCT_xxxxxxxx",
  "bearer": "account",
  "metadata": {
    "order_id": "...",
    "custom_fields": [
      { "display_name": "Order ID", "variable_name": "order_id", "value": "..." }
    ]
  }
}
```

**Notes:**

- `amount` — string integer in **kobo**.
- `reference` — maps to `payments.reference` (our ID, sent to Paystack).
- `subaccount` — seller's `ACCT_...` code.
- `bearer: "account"` — platform (main account) bears Paystack processing fees (default marketplace pattern).
- Optional `transaction_charge` — flat kobo to main account; overrides percentage split for that transaction.
- Response: `data.access_code`, `data.reference` → frontend opens Paystack Inline (`resumeTransaction(access_code)`).

### 3. Verify payment (callback + sweeps)

```
GET https://api.paystack.co/transaction/verify/{reference}
```

Use when:

- Frontend Paystack callback fires before webhook
- Sweeping stale `PENDING` payments / abandoned checkout

**Must verify before marking PAID:**

- `data.status === "success"`
- `data.amount` matches expected kobo
- `data.currency === "NGN"`
- `data.reference` matches `payments.reference`

### 4. Refund

```
POST https://api.paystack.co/refund
```

**Body:**

```json
{
  "transaction": "PAY-abc123",
  "amount": 1000000
}
```

**Split refund behaviour (critical):**

- Refund is always debited from the **main/integration account balance**, not clawed back from the subaccount automatically.
- If seller share was **already settled** to seller bank, platform is out of pocket until recovered from seller manually.
- **Manual settlement before release** is the whole point of escrow — refunds while funds are still held avoid settled-split clawback complexity.
- Webhooks: `refund.pending`, `refund.processing`, `refund.processed`, `refund.failed` (not only `processed`).
- Some refunds enter `needs-attention` (requires customer bank details via Retry Refund API).

### 5. Settlement (read-only API)

```
GET https://api.paystack.co/settlement
GET https://api.paystack.co/settlement/{id}/transactions
```

Query param `subaccount` filters settlements for a subaccount. Used for **reconciliation**, not release.

### 6. Webhooks

**Route:** `POST /webhooks/paystack` (add to auth public paths — exact path only)

**Handle in Phase 1+:**

| Event | Purpose |
| ----- | ------- |
| `charge.success` | Mark payment PAID, create escrow HELD, deduct stock |
| `charge.dispute.create` / `.remind` / `.resolve` | Block/release settlement; chargeback risk |
| `refund.processed` / `.failed` / `.pending` / `.processing` | Payment refund lifecycle |
| Settlement-related | TBD after release spike (see open question below) |

**Do NOT rely on:**

- `charge.failed` — **does not exist**. Failed/abandoned checkout detected via verify + pending sweep.

**Idempotency:**

- Payload shape: `{ "event": "...", "data": { "id": ..., ... } }` — no top-level event ID.
- Dedupe key: `sha256(raw_body)` or composite `(event, data.id, data.status)` stored in `payment_events.provider_event_id`.
- State transitions must also be conditional (`UPDATE ... WHERE status = expected`).

**Signature verification:**

```python
import hashlib, hmac

expected = hmac.new(
    secret_key.encode("utf-8"),
    raw_body,
    hashlib.sha512,
).hexdigest()
# compare to request.headers["x-paystack-signature"]
```

Read `await request.body()` **before** JSON parsing.

**`charge.success` split payload** (multi-split; single subaccount similar):

```json
{
  "event": "charge.success",
  "data": {
    "id": 697123356,
    "reference": "PAY-abc123",
    "amount": 1000000,
    "fees": 15000,
    "split": {
      "shares": {
        "paystack": 140,
        "integration": 7860,
        "subaccounts": [
          { "subaccount_code": "ACCT_xxx", "amount": 200000 }
        ]
      }
    }
  }
}
```

Store `data.fees` on payment row for economics (`provider_fee_amount` or plain `fee_amount` column TBD in Phase 1).

---

## Open question — escrow release API (Phase 0 blocker for Phase 4)

**Question:** How do we programmatically **trigger manual settlement** for a specific transaction's subaccount share?

**Research result:**

| Source | Claim |
| ------ | ----- |
| Paystack Subaccount API docs | `settlement_schedule: manual` means payout "only when requested" |
| Paystack Settlement API docs | **GET only** — list settlements and transactions; no create/trigger endpoint documented |
| Third-party marketplace guides | "Trigger settlement via API or dashboard" — **no canonical endpoint cited** |
| Some aggregator docs | Fallback: Transfers from platform balance (contradicts split-direct-settlement model) |

**Recommended validation (before Phase 4):**

1. Create test subaccount with `settlement_schedule: manual`
2. Run test split transaction in Paystack **test mode**
3. Inspect dashboard: is subaccount share shown as "pending settlement"?
4. Contact Paystack support / account manager: **exact API or dashboard action to release one transaction's subaccount share**
5. If per-transaction API exists but is undocumented, capture curl example in this doc

**Interim fallbacks if no per-transaction API:**

| Fallback | Tradeoff |
| -------- | -------- |
| Dashboard manual settlement (ops) | Not scalable; OK for MVP dogfood |
| Batch settlement API (if exists) | May not map 1:1 to order release timing |
| Paystack Connect onboarding call | May unlock settlement controls not in public docs |

**Plan impact:** Phase 4 (release job) **depends on closing this question**. Phases 1–3 can proceed without it.

---

## Economics (missing from original plan — add in Phase 1)

Paystack NGN card fees (~1.5% + ₦100, capped) come out of whoever bears fees (`bearer: account` → platform).

Example order ₦10,000 (1,000,000 kobo), 5% platform fee:

| Party | Gross share | After Paystack fee (approx) |
| ----- | ----------- | --------------------------- |
| Platform | ₦500 | ₦500 − ~₦250 fee ≈ ₦250 net |
| Seller (held) | ₦9,500 | Seller share not fee-bearing if `bearer: account` |

**Phase 1 schema addition:** store `fee_amount` (from `charge.success` `data.fees`) on `payments`. Document rounding: compute split in kobo integers; `platform_fee + seller_net == amount` before fees.

---

## Stock oversell (Phase 1 design choice required)

Deferring stock deduction to `charge.success` allows two customers to pay for the last unit.

**Pick one before Phase 1 ships paid checkout:**

| Option | Mechanism |
| ------ | --------- |
| **A — Stock reservation** | Reserve at `POST /orders` (paid path); TTL sweep releases; deduct on payment confirm |
| **B — Auto-refund on oversell** | On `charge.success`, if deduct fails → initiate Paystack refund; never return 422 from webhook handler |

Expert review recommends explicit choice; webhook must **always return 200** to Paystack after logging failure.

---

## Escrow state machine corrections (from expert review)

Add **`RELEASING`** state to `escrow_holds.status` before Phase 4:

```
RELEASE_PENDING → RELEASING → RELEASED
```

Release job must:

1. Conditional claim: `UPDATE ... SET status='RELEASING' WHERE status='RELEASE_PENDING' AND release_at <= now()`
2. Idempotent settlement trigger keyed on `escrow_hold.id` (deterministic reference if API supports it)
3. Single scheduler leader (not APScheduler per uvicorn worker without distributed lock)

Pin `RELEASE_PENDING` entry to **synchronous** seller status PATCH (`DELIVERED` / `PICKED_UP`), not a separate escrow job.

---

## Phase 0 prerequisites checklist (Paystack dashboard)

Before Phase 2 (seller subaccounts) in **live** mode:

- [ ] Business verification complete
- [ ] Transfers product enabled (fallback path)
- [ ] Transfer OTP disabled for programmatic use (if transfers needed)
- [ ] Webhook URL configured (test + live separately)
- [ ] Confirm manual settlement supported for subaccounts on this integration (support ticket)
- [ ] Confirm maximum hold duration for manual settlement (marketplace policy)

---

## Recommended plan updates (applied to main plan)

1. Remove `charge.failed` from webhook handler scope
2. Remove `PAYSTACK_WEBHOOK_SECRET` — use secret key for signing
3. Add Phase 0 gate: live test settlement trigger before Phase 4
4. Add stock reservation **or** auto-refund decision to Phase 1
5. Add `RELEASING` escrow state + conditional claim pattern to Phase 4
6. Add dispute webhooks (`charge.dispute.*`) to Phase 5 minimum
7. Add `fee_amount` column on payments
8. Document `percentage_charge` semantics (seller share, not platform share)

---

## Phase 1 entry criteria (Phase 0 exit)

- [x] API endpoints documented for subaccount create, transaction initialize, verify, refund
- [x] Webhook events and signing documented
- [x] Split refund limitations documented
- [ ] **Settlement trigger validated** in Paystack test mode (owner: needs test API keys)
- [ ] Stock strategy chosen (reservation vs auto-refund)

**Next step:** Obtain Paystack test keys → run scripted test in `tests/paystack_spike/` or manual curl checklist → update "Open question" section with confirmed release API.

---

## Quick reference — curl smoke test (test mode)

Replace `sk_test_...` and bank details with valid test values.

```bash
# 1. Resolve account
curl "https://api.paystack.co/bank/resolve?account_number=0123456789&bank_code=058" \
  -H "Authorization: Bearer sk_test_xxx"

# 2. Create subaccount (manual settlement)
curl https://api.paystack.co/subaccount \
  -H "Authorization: Bearer sk_test_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Test Seller",
    "settlement_bank": "058",
    "account_number": "0123456789",
    "percentage_charge": 95,
    "settlement_schedule": "manual"
  }'

# 3. Initialize split payment
curl https://api.paystack.co/transaction/initialize \
  -H "Authorization: Bearer sk_test_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "amount": "500000",
    "reference": "PAY-SPIKE-001",
    "subaccount": "ACCT_xxx",
    "bearer": "account"
  }'

# 4. After test payment — verify
curl "https://api.paystack.co/transaction/verify/PAY-SPIKE-001" \
  -H "Authorization: Bearer sk_test_xxx"

# 5. List settlements for subaccount (reconciliation)
curl "https://api.paystack.co/settlement?subaccount=ACCT_xxx" \
  -H "Authorization: Bearer sk_test_xxx"
```

---

## Related documents

- Implementation plan: `.cursor/plans/paystack_escrow_payment_flow_90eebd79.plan.md`
- Expert review: [`docs/paystack-escrow-plan-review.html`](paystack-escrow-plan-review.html)
- Paystack split payments: https://paystack.com/docs/payments/split-payments/
- Paystack subaccount API: https://paystack.com/docs/api/subaccount/
- Paystack refunds: https://paystack.com/docs/payments/refunds/
