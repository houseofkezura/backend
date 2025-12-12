# Frontend Integration Guide (Kezura BFF)

Concise guide for frontend devs and LLM agents on how to call the BFF. All requests are JSON; include `Content-Type: application/json`.

## Authentication & Authorization
- Auth provider: **Clerk**. Send `Authorization: Bearer <clerk_token>` with every protected call.
- Backend validates token and sets `g.current_user`. Role-based access via:
  - `@customer_required` for customer endpoints.
  - `@roles_required(...)` / `@admin_required` for admin endpoints.
- Roles: `Super Admin`, `Admin`, `Operations`, `CRM Manager`, `Finance`, `Support`, `Customer`.

## Public Auth Endpoints (`/api/v1/public/auth`)
> Clerk is the source of truth. These exist mainly for compatibility.

- `POST /auth/login` *(Deprecated)*  
  Request: `{ "email_username": "user@example.com", "password": "secret" }`  
  Response: `410 Gone` (use Clerk).

- `POST /auth/signup`  
  Body: `SignUpRequest` → `{ email, firstname, lastname?, username?, password }`  
  Flow: sends verification code; returns `{ reg_id }`.

- `POST /auth/verify-email`  
  Body: `{ reg_id, code }` → creates user + Clerk account; returns `{ user_data }`.

- `POST /auth/validate-token`  
  Header: `Authorization: Bearer <clerk_token>`  
  Response: `{ valid: true, user_data }`

- `POST /auth/refresh-token`  
  Info only; Clerk handles refresh.

- `POST /auth/change-password` *(protected)*  
  Body: `{ current_password, new_password }`  
  Also sets `has_updated_default_password = true`.

- `POST /auth/forgot-password` → `{ email }`  
- `POST /auth/verify-password-reset-code` → `{ reset_id, code }`  
- `POST /auth/reset-password` → `{ reset_id, code, new_password }` (sets `has_updated_default_password = true`)

- `GET /auth/me` *(protected)*  
  Response: `{ user: { id, email, roles, has_updated_default_password, loyalty? ... } }`

## Customer-Facing (high level)
Key flows (all require Clerk bearer token unless guest is allowed):
- Products: `GET /products`, `GET /products/:slug`
- Cart: `GET /cart`, `POST /cart/items`, `PUT /cart/items/:id`, `DELETE /cart/items/:id`
- Checkout: `POST /checkout`
  - Guests allowed; must pass `email`, `phone`, `shipping_address`.
  - Optional `idempotency_key` to safely retry.
  - If total between ₦200k–₦500k, guest account auto-created with generated password (prefixed by `DEFAULT_GUEST_PREFIX_...`) and role `Customer`, tier `Muse`, `has_updated_default_password = false`.
- Orders: `GET /orders/:id`, `GET /orders?user_id=`
- Loyalty: `GET /loyalty/me`, `POST /loyalty/redeem`

## Admin Auth & RBAC
- Verify admin token/roles: `GET /api/v1/admin/auth/verify` (requires any admin role).
- All admin routes use `SecurityScheme.ADMIN_BEARER` and `roles_required/admin_required`.

## Admin Endpoints (selected)
Headers: `Authorization: Bearer <clerk_token>`

### Products (`/api/v1/admin/products`)
- `GET /products` – list (filters via query).
- `GET /products/{id}` – get one.
- `POST /products` – create product (+optional variants).  
  Body: `CreateProductRequest` → `{ name, slug?, description?, category, metadata?, meta_title?, meta_description?, meta_keywords?, launch_status?, variants?: [ { sku, price_ngn, price_usd?, weight_g?, attributes, media_ids? } ] }`
- `PATCH /products/{id}` – update; body: `UpdateProductRequest`.
- `DELETE /products/{id}` – delete.
- Variant CRUD: `POST /products/{id}/variants`, `PATCH /products/{id}/variants/{variant_id}`, `DELETE /products/{id}/variants/{variant_id}` (bodies use `CreateProductVariantRequest` / `UpdateProductVariantRequest`).

### Inventory (`/api/v1/admin/inventory`)
- `GET /inventory` – list; query: `low_stock_only`, `sku`, `page`, `per_page`.
- `GET /inventory/sku/{sku}` – view by SKU.
- `POST /inventory/adjust` – body: `{ variant_id, quantity, adjust_delta?, low_stock_threshold? }`.

### Orders (`/api/v1/admin/orders`)
- `GET /orders` – filters: `status`, `user_id`, `search`, pagination.
- `GET /orders/{id}`
- `PATCH /orders/{id}/status` – body: `{ status, notes? }`.
- `POST /orders/{id}/cancel`

### Users & Roles (`/api/v1/admin/users`)
- `GET /users` – filters: `search`, `role`, pagination.
- `GET /users/{id}`
- `POST /users/{id}/roles` – body: `{ role }` (assign).
- `DELETE /users/{id}/roles` – body: `{ role }` (revoke).
- `POST /users/{id}/deactivate`

### Loyalty (`/api/v1/admin/loyalty`)
- `GET /loyalty/accounts`
- `POST /loyalty/accounts/{account_id}/adjust` – body: `{ points, reason? }`

### Staff (`/api/v1/admin/staff`)
- `GET /staff`
- `POST /staff` – body: `{ name, staff_code, contact?, role? }`

### CMS (`/api/v1/admin/cms`)
- `GET /cms/pages`
- `POST /cms/pages` – body: `{ slug, title, content, published? }`
- `PATCH /cms/pages/{id}` – body: `{ slug?, title?, content?, published? }`
- `DELETE /cms/pages/{id}`

### B2B (`/api/v1/admin/b2b`)
- `GET /b2b/inquiries` – filters: `status`, pagination.
- `PATCH /b2b/inquiries/{id}/status` – body: `{ status?, note? }`

### CRM Ratings (`/api/v1/admin/crm`)
- `GET /crm/ratings` – filters: `staff_id`, pagination.

### Revamps (`/api/v1/admin/revamps`)
- `GET /revamps`
- `PATCH /revamps/{id}/status` – body: `{ status?, assigned_to? }`

## Headers & Formats
- Always send `Content-Type: application/json`.
- Auth header: `Authorization: Bearer <clerk_token>`.
- Pagination: `page`, `per_page` query params.
- Errors: standardized `{ "success": false, "message": "...", "data": null }` via `ErrorResponse`.

## Sample Authenticated Call
```bash
curl -X GET https://api.example.com/api/v1/admin/products \
  -H "Authorization: Bearer <clerk_token>" \
  -H "Content-Type: application/json"
```

## Idempotent Checkout (example)
```bash
curl -X POST https://api.example.com/api/v1/public/checkout \
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





