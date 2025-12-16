# Frontend Integration Guide (Kezura BFF)

All requests are JSON; send `Content-Type: application/json`.

## How Auth Works (Plain English)
- Identity provider: **Clerk**. Frontend gets Clerk session/JWT tokens via Clerk SDK.
- Frontend responsibility:
  - Acquire Clerk token after login/signup.
  - Send `Authorization: Bearer <clerk_token>` on every protected request.
  - Handle Clerk-driven refresh; backend does not mint access tokens.
- Backend responsibility:
  - Validate the Clerk token (session or JWT) on every protected call.
  - Link the Clerk user to our `AppUser` (create/update if missing).
  - Attach the user as `g.current_user` and enforce roles.
- Roles: `Super Admin`, `Admin`, `Operations`, `CRM Manager`, `Finance`, `Support`, `Customer`.
- Decorators that guard routes:
  - `@customer_required` (and alias `@public_auth_required`): any authenticated user.
  - `@roles_required(...)` / `@admin_required`: role-checked access.

### Request/Response Contract for Protected Calls
- Headers to send:
  - `Authorization: Bearer <clerk_token>`
  - `Content-Type: application/json`
- What backend does per request:
  1) Reads the bearer token.
  2) Validates it with Clerk (session verify → JWT verify with Clerk JWKS).
  3) Loads or creates `AppUser` mapped to `clerk_id`; syncs email/profile if changed.
  4) Stores user in `g.current_user`.
  5) Checks roles when required; returns 401/403 on failure.
- Expected errors:
  - 401 Missing/invalid/expired token.
  - 403 Token ok but roles insufficient.

### Public Auth Endpoints (`/api/v1/auth`)
> Clerk is source of truth; these exist for compatibility and password flows.

- `POST /auth/login` *(Deprecated)* → returns `410 Gone` (use Clerk SDK).
- `POST /auth/signup` → `{ email, firstname, lastname?, username?, password }`  
  Sends email code; returns `{ reg_id }`.
- `POST /auth/verify-email` → `{ reg_id, code }`  
  Creates `AppUser`, profile, address, default `Customer` role, Clerk user; returns `{ user_data }`.
- `POST /auth/validate-token` *(protected)*  
  Header: bearer token. Returns `{ valid: true, user_data }`.
- `POST /auth/refresh-token` → Info only; Clerk handles refresh.
- `POST /auth/change-password` *(protected)* → `{ current_password, new_password }`; sets `has_updated_default_password = true`.
- Password reset flow:
  - `POST /auth/forgot-password` → `{ email }`
  - `POST /auth/verify-password-reset-code` → `{ reset_id, code }`
  - `POST /auth/reset-password` → `{ reset_id, code, new_password }` (also sets `has_updated_default_password = true`)
- `GET /auth/me` *(protected)* → `{ user: { id, email, roles, has_updated_default_password, loyalty?... } }`

### Quick Integration Steps (Frontend)
1) Use Clerk UI/SDK to log users in and obtain the latest bearer token.
2) Attach `Authorization: Bearer <clerk_token>` to every protected request.
3) On 401: refresh token via Clerk SDK and retry; if still failing, re-auth.
4) On 403: surface “insufficient permissions” to the user (roles mismatch).
5) For password flows (change/reset), call the listed endpoints; tokens still required where marked “protected”.

## Customer-Facing (high level)
- Products: `GET /products`, `GET /products/:slug`
- Cart: `GET /cart`, `POST /cart/items`, `PUT /cart/items/:id`, `DELETE /cart/items/:id`
- Checkout: `POST /checkout`
  - Guests allowed; must pass `email`, `phone`, `shipping_address`.
  - Optional `idempotency_key` to safely retry.
  - If total between ₦200k–₅₀₀k, guest account auto-created with generated password (prefixed `DEFAULT_GUEST_PREFIX_...`), role `Customer`, tier `Muse`, `has_updated_default_password = false`.
- Orders: `GET /orders/:id`, `GET /orders?user_id=`
- Loyalty: `GET /loyalty/me`, `POST /loyalty/redeem`

## Admin Auth & RBAC
- Verify admin token/roles: `GET /api/v1/admin/auth/verify` (needs any admin role).
- All admin routes use bearer tokens plus `roles_required/admin_required`.

## Admin Endpoints (selected)
Headers: `Authorization: Bearer <clerk_token>`

### Products (`/api/v1/admin/products`)
- `GET /products` – list (filters via query).
- `GET /products/{id}` – get one.
- `POST /products` – create product (+optional variants).  
  Body: `CreateProductRequest` → `{ name, slug?, description?, category, metadata?, meta_title?, meta_description?, meta_keywords?, launch_status?, variants?: [ { sku, price_ngn, price_usd?, weight_g?, attributes, media_ids? } ] }`
- `PATCH /products/{id}` – update; body: `UpdateProductRequest`.
- `DELETE /products/{id}` – delete.
- Variant CRUD: `POST /products/{id}/variants`, `PATCH /products/{id}/variants/{variant_id}`, `DELETE /products/{id}/variants/{variant_id}`.

### Inventory (`/api/v1/admin/inventory`)
- `GET /inventory` – list; query: `low_stock_only`, `sku`, `page`, `per_page`.
- `GET /inventory/sku/{sku}` – view by SKU.
- `POST /inventory/adjust` – `{ variant_id, quantity, adjust_delta?, low_stock_threshold? }`.

### Orders (`/api/v1/admin/orders`)
- `GET /orders` – filters: `status`, `user_id`, `search`, pagination.
- `GET /orders/{id}`
- `PATCH /orders/{id}/status` – `{ status, notes? }`.
- `POST /orders/{id}/cancel`

### Users & Roles (`/api/v1/admin/users`)
- `GET /users` – filters: `search`, `role`, pagination.
- `GET /users/{id}`
- `POST /users/{id}/roles` – `{ role }` (assign).
- `DELETE /users/{id}/roles` – `{ role }` (revoke).
- `POST /users/{id}/deactivate`

### Loyalty (`/api/v1/admin/loyalty`)
- `GET /loyalty/accounts`
- `POST /loyalty/accounts/{account_id}/adjust` – `{ points, reason? }`

### Staff (`/api/v1/admin/staff`)
- `GET /staff`
- `POST /staff` – `{ name, staff_code, contact?, role? }`

### CMS (`/api/v1/admin/cms`)
- `GET /cms/pages`
- `POST /cms/pages` – `{ slug, title, content, published? }`
- `PATCH /cms/pages/{id}` – `{ slug?, title?, content?, published? }`
- `DELETE /cms/pages/{id}`

### B2B (`/api/v1/admin/b2b`)
- `GET /b2b/inquiries` – filters: `status`, pagination.
- `PATCH /b2b/inquiries/{id}/status` – `{ status?, note? }`

### CRM Ratings (`/api/v1/admin/crm`)
- `GET /crm/ratings` – filters: `staff_id`, pagination.

### Revamps (`/api/v1/admin/revamps`)
- `GET /revamps`
- `PATCH /revamps/{id}/status` – `{ status?, assigned_to? }`

## Headers & Formats
- Always send `Content-Type: application/json`.
- Auth header: `Authorization: Bearer <clerk_token>`.
- Pagination: `page`, `per_page` query params.
- Errors: standardized `{ "success": false, "message": "...", "data": null }`.

## Sample Authenticated Call
```bash
curl -X GET https://api.example.com/api/v1/admin/products \
  -H "Authorization: Bearer <clerk_token>" \
  -H "Content-Type: application/json"
```

## Idempotent Checkout (example)
```bash
curl -X POST https://api.example.com/api/v1/checkout \
  -H "Authorization: Bearer <clerk_token_or_guest_optional>" \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "uuid",
    "shipping_address": { "country": "NG", "state": "Lagos", "full_name": "Ada", "phone": "+234..." },
    "payment_method": "card",
    "payment_token": "tok_xxx",
    "idempotency_key": "req-123",
    "email": "guest@example.com",
    "phone": "+234...",
    "first_name": "Ada",
    "last_name": "Obi"
  }'
```





