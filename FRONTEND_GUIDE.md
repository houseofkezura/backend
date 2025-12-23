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
  Public endpoints return products with fields: `id`, `name`, `sku`, `slug`, `description`, `category`, `care`, `details`, `material`, `status`, `images`, `image_urls`, `variants` (with pricing, attributes, inventory, images).
- Variants: `GET /products/variants/:variant_id`  
  Get a single variant by ID with inherited product information (description, care, materials, product images). Returns variant-specific images and product images separately.
- Cart: `GET /cart`, `POST /cart/items`, `PUT /cart/items/:id`, `DELETE /cart/items/:id`  
  Supports authenticated users and guests. Guest tokens are preserved across requests - store the token from the first response and reuse it. Cart items include variant images and product information.
- Wishlist: `GET /wishlist`, `POST /wishlist/items`, `DELETE /wishlist/items/:id`, `GET /wishlist/check/:variant_id`  
  Authenticated-only. Returns variant images, product images, and inherited product fields (description, care, materials).
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
  Body: `CreateProductRequest` → `{ name, sku?, slug?, description?, category, care?, details?, material?, metadata?, meta_title?, meta_description?, meta_keywords?, status? (default: "In-Stock"), launch_status? (legacy), variants?: [ { sku, price_ngn, price_usd?, weight_g?, attributes, media_ids? } ] }`  
  **Note**: `sku` is optional and will be auto-generated from product name if not provided. If provided, must be unique. `status` is preferred over `launch_status`.
- `PATCH /products/{id}` – update; body: `UpdateProductRequest` (all fields optional, `sku` must be unique if provided).
- `DELETE /products/{id}` – delete.
- Variant CRUD: `POST /products/{id}/variants`, `PATCH /products/{id}/variants/{variant_id}`, `DELETE /products/{id}/variants/{variant_id}`.

**Product Fields:**
- `sku` (string, optional, unique): Product SKU identifier (auto-generated from name if not provided)
- `name` (string, required): Product name
- `slug` (string, optional): URL-friendly slug (auto-generated from name if not provided)
- `description` (string, optional): Product description
- `category` (string, required): Product category
- `care` (string, optional): Product care instructions
- `details` (string, optional): Product details
- `material` (string, optional): Product material
- `status` (string, optional, default: "In-Stock"): Product status (preferred over `launch_status`)
- `launch_status` (string, optional, legacy): Use `status` instead
- `metadata` (object, optional): Additional metadata
- `meta_title`, `meta_description`, `meta_keywords` (strings, optional): SEO fields

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
  -H "Idempotency-Key: req-123" \
  -d '{
    "cart_id": "uuid",
    "shipping_address": { "country": "NG", "state": "Lagos", "full_name": "Ada", "phone": "+234..." },
    "payment_method": "card",
    "email": "guest@example.com",
    "phone": "+234...",
    "first_name": "Ada",
    "last_name": "Obi"
  }'
```

### Get Variant by ID

**Endpoint:** `GET /api/v1/public/products/variants/{variant_id}`

**Description:** Get a single variant by ID with inherited product information. Variants inherit fields from their parent product (description, care, materials) and include both variant-specific images and product images.

**Request:**
- No authentication required (public endpoint)
- Path parameter: `variant_id` (UUID)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Variant retrieved successfully",
  "data": {
    "variant": {
      "id": "uuid",
      "product_id": "uuid",
      "sku": "KZ-WG-0A12-32BLK",
      "price_ngn": 50000.00,
      "price_usd": 50.00,
      "price": 50000.00,
      "color": "Black",
      "stock": 10,
      "is_in_stock": true,
      "attributes": {
        "color": "Black",
        "length": "32",
        "texture": "Straight"
      },
      "images": [
        {
          "id": "uuid",
          "file_url": "https://cloudinary.com/...",
          "thumbnail_url": "https://cloudinary.com/..."
        }
      ],
      "image_urls": ["https://cloudinary.com/..."],
      // Inherited from product
      "product_name": "Kezura Mav Bone Straight Hair",
      "product_slug": "kezura-mav-bone-straight-hair",
      "product_category": "Wigs",
      "description": "Premium bone straight hair extension",
      "care": "Detangle gently with wide-tooth comb",
      "details": "100% human hair, virgin quality",
      "material": "Human Hair",
      "product_images": [
        {
          "id": "uuid",
          "file_url": "https://cloudinary.com/..."
        }
      ],
      "product_image_urls": ["https://cloudinary.com/..."]
    }
  }
}
```

**Note:** 
- Variants inherit `description`, `care`, `details`, and `material` from their parent product
- Variants have their own `images` array (variant-specific images)
- Variants also include `product_images` array (inherited from product)
- Use `image_urls` and `product_image_urls` for simple URL arrays

### Cart Management

**Endpoint:** `GET /api/v1/cart`

**Description:** Get the current user's cart or guest cart. Supports multiple lookup methods:
- By authenticated user (automatic)
- By guest token (header `X-Guest-Token` or query param `guest_token`)
- By cart ID (query param `cart_id`)

**Guest Token Management:**
- **CRITICAL**: Guest tokens are preserved across requests. Store the token from the first cart response and reuse it.
- First request: Store `guest_token` from response (localStorage/sessionStorage)
- Subsequent requests: Send token via `X-Guest-Token` header or `guest_token` query param
- Token only changes if not provided (new guest session)

**Request Headers (for guests):**
- `X-Guest-Token: <token>` (recommended)

**Query Parameters:**
- `cart_id` (optional): Cart UUID to fetch specific cart
- `guest_token` (optional): Alternative to header (for guests)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Cart retrieved successfully",
  "data": {
    "cart": {
      "id": "uuid",
      "user_id": null,
      "guest_token": "abc123...",
      "items": [
        {
          "id": "uuid",
          "variant_id": "uuid",
          "quantity": 2,
          "unit_price": 50000.00,
          "line_total": 100000.00,
          "variant": {
            "id": "uuid",
            "sku": "KZ-WG-0A12-32BLK",
            "price_ngn": 50000.00,
            "price": 50000.00,
            "color": "Black",
            "stock": 10,
            "images": [
              {
                "id": "uuid",
                "file_url": "https://cloudinary.com/...",
                "thumbnail_url": "https://cloudinary.com/..."
              }
            ],
            "image_urls": ["https://cloudinary.com/..."],
            "product_name": "Kezura Mav Bone Straight Hair",
            "product_slug": "kezura-mav-bone-straight-hair",
            "description": "Premium bone straight hair extension",
            "care": "Detangle gently",
            "material": "Human Hair",
            "product_images": [...],
            "product_image_urls": [...]
          }
        }
      ],
      "total_items": 2,
      "subtotal": 100000.00
    },
    "guest_token": "abc123..."
  }
}
```

**Example (JavaScript):**
```javascript
// First request - store token
const response = await fetch('/api/v1/cart');
const { guest_token } = await response.json();
localStorage.setItem('guest_token', guest_token);

// Subsequent requests - reuse token
const token = localStorage.getItem('guest_token');
const cartResponse = await fetch('/api/v1/cart', {
  headers: { 'X-Guest-Token': token }
});

// Or use query param
const cartResponse2 = await fetch(`/api/v1/cart?guest_token=${token}`);

// Or get by cart ID (if you have it)
const cartResponse3 = await fetch(`/api/v1/cart?cart_id=${cartId}`);
```

**Add Item to Cart:** `POST /api/v1/cart/items`
- Body: `{ variant_id, quantity, guest_token? }`
- Headers: `X-Guest-Token` (for guests)
- Returns updated cart with `guest_token` (preserve this token!)

**Update Cart Item:** `PUT /api/v1/cart/items/{item_id}`
- Body: `{ quantity }`
- Headers: `X-Guest-Token` (for guests)

**Remove Cart Item:** `DELETE /api/v1/cart/items/{item_id}`
- Headers: `X-Guest-Token` (for guests)

### Wishlist Management

**Endpoint:** `GET /api/v1/wishlist`

**Description:** Get authenticated user's wishlist. Returns paginated results with full variant data including images and product information.

**Request:**
- Requires authentication (`Authorization: Bearer <token>`)
- Query params: `page` (default: 1), `per_page` (default: 20, max: 100)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Wishlist retrieved successfully",
  "data": {
    "items": [
      {
        "id": "uuid",
        "variant_id": "uuid",
        "variant": {
          "id": "uuid",
          "sku": "KZ-WG-0A12-32BLK",
          "price_ngn": 50000.00,
          "price": 50000.00,
          "color": "Black",
          "stock": 10,
          "is_in_stock": true,
          "attributes": {
            "color": "Black",
            "length": "32"
          },
          "images": [
            {
              "id": "uuid",
              "file_url": "https://cloudinary.com/...",
              "thumbnail_url": "https://cloudinary.com/..."
            }
          ],
          "image_urls": ["https://cloudinary.com/..."],
          "product": {
            "id": "uuid",
            "name": "Kezura Mav Bone Straight Hair",
            "slug": "kezura-mav-bone-straight-hair"
          },
          "product_name": "Kezura Mav Bone Straight Hair",
          "product_slug": "kezura-mav-bone-straight-hair",
          "product_category": "Wigs",
          "description": "Premium bone straight hair extension",
          "care": "Detangle gently",
          "details": "100% human hair",
          "material": "Human Hair",
          "product_images": [...],
          "product_image_urls": [...]
        },
        "created_at": "2025-12-22T10:00:00Z"
      }
    ],
    "total": 5,
    "current_page": 1,
    "total_pages": 1
  }
}
```

**Add to Wishlist:** `POST /api/v1/wishlist/items`
- Body: `{ variant_id }`
- Returns wishlist item with full variant data including images

**Remove from Wishlist:** `DELETE /api/v1/wishlist/items/{item_id}`

**Check if in Wishlist:** `GET /api/v1/wishlist/check/{variant_id}`
- Returns: `{ variant_id, is_in_wishlist, wishlist_item_id? }`

### End-to-end flow (frontend)
1) Browse & cart  
   - `GET /api/v1/products` (filters: `category`, `search`, `in_stock_only`, `page`, `per_page`)  
     Returns products with: `id`, `name`, `sku`, `slug`, `description`, `category`, `care`, `details`, `material`, `status`, `images`, `image_urls`, `variants` (with `price_ngn`, `price_usd`, `attributes`, `is_in_stock`, `stock_quantity`, `images`, `image_urls`).
   - `POST /api/v1/cart/items` (include `guest_token` in body or `X-Guest-Token` header for guests)  
     **IMPORTANT**: Store the `guest_token` from the response for subsequent requests.
   - `GET /api/v1/cart` (include `X-Guest-Token` header for guests)
2) Shipping quote  
   - `GET /api/v1/shipping/zones?country=NG` to show costs/ETA.
3) Checkout (creates order + payment session)  
   - `POST /api/v1/checkout` with `cart_id`/`guest_token`, shipping address, contact, optional points, `Idempotency-Key` header.  
   - Response: `{ order_id, payment_status, payment_reference, authorization_url }` (order is `pending_payment`).
4) Redirect to pay  
   - Open `authorization_url` (Paystack/Flutterwave/BitPay). Keep `payment_reference`.
5) Confirm payment  
   - After gateway redirect: `POST /api/v1/payment/verify { "reference": "<payment_reference>" }`.  
   - Webhook also hits `/api/v1/payment/webhook` (source of truth). If verify lags, poll `GET /api/v1/orders/{order_id}` until `status = "paid"`.
6) Post-payment UX  
   - Show success, clear local cart, fetch `GET /api/v1/orders/{order_id}` for summary.

### Notes
- Guests can pay; verify works with just the `reference`.  
- Use `Idempotency-Key` on checkout to retry safely.  
- Order stays `pending_payment` until verify/webhook marks it `paid`.  