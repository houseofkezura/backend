# Kezura BFF

## Authentication (Clerk)
- Clerk is the sole auth provider. Clients send `Authorization: Bearer <token>` (Clerk session/JWT).
- Server validates tokens via `app/utils/auth/clerk.py` and normalizes the user to `g.current_user`.
- Decorators:
  - `@customer_required` for authenticated customer endpoints (sets `g.current_user`).
  - `@roles_required(...)` / `@admin_required` for RBAC-protected admin endpoints.
- Public auth routes (`/api/v1/public/auth`):
  - Legacy signup/verify flows remain, but password issuance/refresh are deprecated; Clerk is authoritative.
  - `change-password`, `reset-password` update `has_updated_default_password` to signal frontend prompts.
- Admin auth: `/api/v1/admin/auth/verify` validates token + roles using Clerk.

## API Docs
- `quas-docs` is wired; every JSON body endpoint declares `request_body` with the corresponding Pydantic schema.
- Swagger/Redoc served via `quas-docs` (see `app/extensions/docs.py`).

## Idempotency
- Checkout supports `idempotency_key`; results cached for 24h to prevent duplicate orders.

## Roles / RBAC
- Roles in `app/enums/auth.py`; RBAC enforced via decorators.
- Admin routes use `SecurityScheme.ADMIN_BEARER` and `@roles_required`/`@admin_required`.

## Guest Checkout & Auto-Accounts
- Guests can checkout; orders between ₦200k–₦500k auto-create a Clerk user and `AppUser`, tier “Muse”, with `has_updated_default_password=False`. Password generated with `DEFAULT_GUEST_PREFIX_<random>`.

## Env Vars
- See `ENV_VARS.md` for full list (Clerk keys, DB, mail, Cloudinary, payment, `DEFAULT_GUEST_PREFIX`, etc.).

## Running
- Use `uv` for dependency management.
- Set `CLERK_SECRET_KEY` before running.

## Frontend Integration Guide
- See `FRONTEND_GUIDE.md` for endpoint usage, auth/RBAC expectations, and sample requests.

