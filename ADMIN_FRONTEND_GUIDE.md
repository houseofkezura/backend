# Admin Frontend Integration Guide (Kezura BFF)

This guide provides detailed instructions for building an admin interface using the Kezura BFF API endpoints.

## Table of Contents
1. [Authentication](#authentication)
2. [Product Management](#product-management)
3. [Material Management](#material-management)
4. [Variant Management](#variant-management)
5. [Inventory Management](#inventory-management)
6. [Order Management](#order-management)
7. [User Management](#user-management)
8. [Common Patterns](#common-patterns)

---

## Authentication

### Overview
All admin endpoints require Clerk authentication with appropriate admin roles.

### Required Roles
- **Super Admin**: Full access to all endpoints
- **Admin**: Most endpoints except sensitive operations
- **Operations**: Product, inventory, and order management
- **CRM Manager**: Customer and order management
- **Finance**: Payment and financial operations
- **Support**: Customer support operations

### Authentication Flow

1. **Get Clerk Token**
   ```javascript
   // Using Clerk SDK
   const token = await clerk.session.getToken();
   ```

2. **Send Token in Requests**
   ```javascript
   const headers = {
     'Authorization': `Bearer ${token}`,
     'Content-Type': 'application/json'
   };
   ```

3. **Handle Errors**
   - `401`: Token missing/invalid/expired → Re-authenticate
   - `403`: Insufficient permissions → Show error message

### Verify Admin Access
```http
GET /api/v1/admin/auth/verify
Authorization: Bearer <clerk_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Admin access verified",
  "data": {
    "user": {
      "id": "uuid",
      "email": "admin@example.com",
      "roles": ["Super Admin", "Operations"]
    }
  }
}
```

---

## Product Management

### Understanding Products and Variants

**Product**: The base product (e.g., "Kezura Mav Bone Straight Hair")
- Has: name, SKU, category, description, care instructions, details, material_ids (links to multiple materials), status
- Does NOT have: price, color, stock (these are on variants)

**Variant**: A specific configuration of a product (e.g., "32 inches, Black color")
- Has: SKU, price_ngn, price_usd, color, length, texture, stock, attributes, material_ids (optional list)
- Belongs to: One product
- Can optionally have its own materials, independent of the product's materials

### Create Product

**Endpoint:** `POST /api/v1/admin/products`

**Required Role:** Super Admin, Operations

**Request Body:**
```json
{
  "name": "Kezura Mav Bone Straight Hair",
  "sku": "KZ-WG-0A12",  // Optional - auto-generated if not provided
  "slug": "kezura-mav-bone-straight-hair",  // Optional - auto-generated from name
  "description": "Premium bone straight hair extension",
  "category": "Wigs",  // Required: "Wigs", "Bundles", or "Hair Care"
  "care": "Detangle gently with wide-tooth comb",
  "details": "100% human hair, virgin quality",
  "material_ids": ["uuid1", "uuid2"],  // Optional - link to multiple ProductMaterials
  "status": "In-Stock",  // Optional, default: "In-Stock"
  "meta_title": "SEO Title",  // Optional
  "meta_description": "SEO Description",  // Optional
  "variants": [  // Optional - can create variants later
    {
      "sku": "KZ-WG-0A12-32BLK",
      "price_ngn": 50000.00,
      "price_usd": 50.00,
      "weight_g": 200,
      "attributes": {
        "color": "Black",
        "length": "32",
        "texture": "Straight",
        "lace_type": "13x4",
        "density": "Medium",
        "cap_size": "Medium",
        "hair_type": "Human Hair"
      },
      "media_ids": ["uuid1", "uuid2"]  // Optional
    }
  ]
}
```

**SKU Auto-Generation:**
- Format: `KZ-[CATEGORY]-[4 random alphanumeric]`
- Category codes: `Wigs` → `WG`, `Bundles` → `BD`, `Hair Care` → `HC`
- Example: `KZ-WG-0A12`, `KZ-BD-3F9K`
- If SKU is not provided, it's auto-generated and guaranteed unique

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Product created successfully",
  "data": {
    "product": {
      "id": "uuid",
      "name": "Kezura Mav Bone Straight Hair",
      "sku": "KZ-WG-0A12",
      "slug": "kezura-mav-bone-straight-hair",
      "description": "Premium bone straight hair extension",
      "category": "Wigs",
      "care": "Detangle gently with wide-tooth comb",
      "details": "100% human hair, virgin quality",
      "material_ids": ["uuid"],  // Array of linked material IDs
      "materials": [  // Array of full material objects
        {
          "id": "uuid",
          "name": "100% Human Hair",
          "description": "Premium quality human hair",
          "usage_count": 5
        }
      ],
      "status": "In-Stock",
      "price_ngn": 50000.00,  // Minimum price from variants
      "price_usd": 50.00,  // Minimum price from variants
      "price": 50000.00,  // Alias for price_ngn
      "color": "Black",  // Comma-separated list from variants
      "stock": 10,  // Total stock from all variants
      "images": [],  // Array of image objects (empty initially)
      "image_urls": [],  // Array of image URLs for convenience
      "variants": [
        {
          "id": "uuid",
          "sku": "KZ-WG-0A12-32BLK",
          "price_ngn": 50000.00,
          "price_usd": 50.00,
          "price": 50000.00,
          "color": "Black",
          "stock": 10,
          "stock_quantity": 10,
          "attributes": {
            "color": "Black",
            "length": "32",
            "texture": "Straight"
          },
          "is_in_stock": true,
          "inventory": {
            "quantity": 10,
            "low_stock_threshold": 5,
            "is_low_stock": false
          }
        }
      ]
    }
  }
}
```

**Error Responses:**
- `400`: Validation error (check field requirements)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (insufficient role)
- `409`: Conflict (SKU or slug already exists)
- `500`: Server error

### Update Product

**Endpoint:** `PATCH /api/v1/admin/products/{product_id}`

**Required Role:** Super Admin, Operations

**Request Body:** (All fields optional)
```json
{
  "name": "Updated Product Name",
  "sku": "KZ-WG-NEW1",  // Must be unique if changed
  "description": "Updated description",
  "category": "Bundles",
  "care": "Updated care instructions",
  "details": "Updated details",
  "material_ids": ["uuid1", "uuid2"],  // List of material IDs (use [] to unlink all)
  "status": "Out of Stock",  // Use "status" not "launch_status"
  "meta_title": "Updated SEO Title"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Product updated successfully",
  "data": {
    "product": {
      // Full product object with variants
    }
  }
}
```

### List Products

**Endpoint:** `GET /api/v1/admin/products`

**Required Role:** Super Admin, Admin, Operations

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 20): Items per page
- `search` (optional): Search in name/description
- `category` (optional): Filter by category
- `launch_status` (optional): Filter by status

**Example:**
```http
GET /api/v1/admin/products?page=1&per_page=20&category=Wigs&search=straight
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Products retrieved successfully",
  "data": {
    "products": [
      {
        "id": "uuid",
        "name": "Product Name",
        "sku": "KZ-WG-0A12",
        "category": "Wigs",
        "status": "In-Stock",
        "price_ngn": 50000.00,
        "price": 50000.00,
        "color": "Black, Brown",
        "stock": 25,
        "variants": [/* variant objects */]
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

### Get Single Product

**Endpoint:** `GET /api/v1/admin/products/{product_id}`

**Required Role:** Super Admin, Admin, Operations

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Product retrieved successfully",
  "data": {
    "product": {
      // Full product object with all variants
    }
  }
}
```

### Delete Product

**Endpoint:** `DELETE /api/v1/admin/products/{product_id}`

**Required Role:** Super Admin, Operations

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Product deleted successfully"
}
```

**Note:** Deleting a product also deletes all its variants and inventory records.

### Add Product Images

**Endpoint:** `POST /api/v1/admin/products/{product_id}/images`

**Required Role:** Super Admin, Operations

**Content-Type:** `multipart/form-data`

**Request:**
- Use `FormData` with field name `images` (or `image` for single file)
- Can upload multiple images at once
- Only image files allowed: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`

**Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('images', file1);  // First image
formData.append('images', file2);  // Second image

const response = await fetch(`/api/v1/admin/products/${productId}/images`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
    // Don't set Content-Type - browser will set it with boundary
  },
  body: formData
});
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Successfully uploaded 2 image(s)",
  "data": {
    "product_id": "uuid",
    "images": [
      {
        "id": "uuid",
        "filename": "product-image.jpg",
        "file_url": "https://cloudinary.com/...",
        "thumbnail_url": "https://cloudinary.com/...",
        "file_type": "image",
        "width": 1920,
        "height": 1080
      }
    ],
    "total_images": 2,
    "errors": null
  }
}
```

**Note:** Images are automatically uploaded to Cloudinary and associated with the product. Product responses will include `images` array and `image_urls` array.

### Remove Product Image

**Endpoint:** `DELETE /api/v1/admin/products/{product_id}/images/{image_id}`

**Required Role:** Super Admin, Operations

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Image removed successfully"
}
```

**Note:** This only removes the association between product and image. The media file itself is not deleted.

### Add Variant Images

**Endpoint:** `POST /api/v1/admin/products/{product_id}/variants/{variant_id}/images`

**Required Role:** Super Admin, Operations

**Content-Type:** `multipart/form-data`

**Request:**
- Use `FormData` with field name `images` (or `image` for single file)
- Can upload multiple images at once
- Only image files allowed: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`

**Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('images', file1);
formData.append('images', file2);

const response = await fetch(`/api/v1/admin/products/${productId}/variants/${variantId}/images`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Successfully uploaded 2 image(s)",
  "data": {
    "product_id": "uuid",
    "variant_id": "uuid",
    "images": [
      {
        "id": "uuid",
        "filename": "variant-image.jpg",
        "file_url": "https://cloudinary.com/...",
        "thumbnail_url": "https://cloudinary.com/...",
        "file_type": "image",
        "width": 1920,
        "height": 1080
      }
    ],
    "total_images": 2,
    "errors": null
  }
}
```

**Note:** Variant images are separate from product images. Variants can have their own images while also inheriting product images.

### Remove Variant Image

**Endpoint:** `DELETE /api/v1/admin/products/{product_id}/variants/{variant_id}/images/{image_id}`

**Required Role:** Super Admin, Operations

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Image removed successfully"
}
```

**Note:** This only removes the association between variant and image. The media file itself is not deleted.

---

## Material Management

### Overview

Materials are reusable entities that can be linked to multiple products. Each material tracks its usage count (how many products use it).

### Create Material

**Endpoint:** `POST /api/v1/admin/products/materials`

**Required Role:** Super Admin, Operations

**Request Body:**
```json
{
  "name": "100% Human Hair",  // Required, must be unique
  "description": "Premium quality virgin human hair"  // Optional
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Material created successfully",
  "data": {
    "material": {
      "id": "uuid",
      "name": "100% Human Hair",
      "description": "Premium quality virgin human hair",
      "usage_count": 0,
      "created_at": "2026-02-04T01:00:00Z",
      "updated_at": "2026-02-04T01:00:00Z"
    }
  }
}
```

### List Materials

**Endpoint:** `GET /api/v1/admin/products/materials`

**Required Role:** Super Admin, Admin, Operations

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 50): Items per page
- `search` (optional): Search in material name

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Materials retrieved successfully",
  "data": {
    "materials": [
      {
        "id": "uuid",
        "name": "100% Human Hair",
        "description": "Premium quality virgin human hair",
        "usage_count": 5
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 10,
      "pages": 1
    }
  }
}
```

### Get Single Material

**Endpoint:** `GET /api/v1/admin/products/materials/{material_id}`

**Required Role:** Super Admin, Admin, Operations

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Material retrieved successfully",
  "data": {
    "material": {
      "id": "uuid",
      "name": "100% Human Hair",
      "description": "Premium quality virgin human hair",
      "usage_count": 5,
      "products": [  // Included when fetching single material
        { "id": "uuid", "name": "Curly Wig", "sku": "KZ-WG-0A12" }
      ]
    }
  }
}
```

### Update Material

**Endpoint:** `PATCH /api/v1/admin/products/materials/{material_id}`

**Required Role:** Super Admin, Operations

**Request Body:** (All fields optional)
```json
{
  "name": "Updated Material Name",
  "description": "Updated description"
}
```

### Delete Material

**Endpoint:** `DELETE /api/v1/admin/products/materials/{material_id}`

**Required Role:** Super Admin, Operations

**Note:** Can only delete materials that are not in use (usage_count = 0). Returns 409 Conflict if material is in use.

---

## Variant Management

### Create Variant

**Endpoint:** `POST /api/v1/admin/products/{product_id}/variants`

**Required Role:** Super Admin, Operations

**Request Body:** (Send the variant object directly, NOT wrapped in an array)
```json
{
  "sku": "KZ-WG-0A12-32BLK",  // Required, must be unique
  "price_ngn": 50000.00,  // Required
  "price_usd": 50.00,  // Optional
  "weight_g": 200,  // Optional
  "attributes": {  // Optional but recommended
    "color": "Black",
    "length": "32",
    "texture": "Straight",
    "lace_type": "13x4",
    "density": "Medium",
    "cap_size": "Medium",
    "hair_type": "Human Hair"
  },
  "material_ids": ["uuid1", "uuid2"],  // Optional - link variant to specific materials
  "media_ids": ["uuid1", "uuid2"]  // Optional
}
```

**Important:** 
- Send the variant object **directly** in the request body
- Do NOT wrap it in `{"variants": [...]}` - that format is only for product creation
- The endpoint will automatically handle the wrapped format if sent, but the direct format is preferred

**Important Notes:**
- `attributes` is **optional** - you can create a variant without attributes
- `color` is stored in `attributes.color` - this is how you set the color
- If `attributes` is not provided, it defaults to an empty object `{}`
- The variant will automatically get an inventory record with quantity 0

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Variant created successfully",
  "data": {
    "variant": {
      "id": "uuid",
      "sku": "KZ-WG-0A12-32BLK",
      "product_id": "uuid",
      "price_ngn": 50000.00,
      "price_usd": 50.00,
      "price": 50000.00,
      "color": "Black",  // Extracted from attributes.color
      "stock": 0,  // Initial stock is 0
      "stock_quantity": 0,
      "attributes": {
        "color": "Black",
        "length": "32",
        "texture": "Straight"
      },
      "is_in_stock": false,
      "inventory": {
        "quantity": 0,
        "low_stock_threshold": 5,
        "is_low_stock": true
      }
    }
  }
}
```

### Update Variant

**Endpoint:** `PATCH /api/v1/admin/products/{product_id}/variants/{variant_id}`

**Required Role:** Super Admin, Operations

**Request Body:** (All fields optional)
```json
{
  "sku": "KZ-WG-0A12-32BLK-NEW",  // Must be unique if changed
  "price_ngn": 55000.00,
  "price_usd": 55.00,
  "weight_g": 250,
  "attributes": {
    "color": "Brown",  // Update color here
    "length": "30"
  },
  "media_ids": ["uuid3", "uuid4"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Variant updated successfully",
  "data": {
    "variant": {
      // Updated variant object
    }
  }
}
```

### Delete Variant

**Endpoint:** `DELETE /api/v1/admin/products/{product_id}/variants/{variant_id}`

**Required Role:** Super Admin, Operations

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Variant deleted successfully"
}
```

**Note:** Deleting a variant also deletes its inventory record.

---

## Inventory Management

### Adjust Inventory

**Endpoint:** `POST /api/v1/admin/inventory/adjust`

**Required Role:** Super Admin, Operations

**Request Body:**
```json
{
  "variant_id": "uuid",
  "quantity": 50,  // New quantity or delta
  "adjust_delta": false,  // If true, adds/subtracts from current
  "low_stock_threshold": 10  // Optional
}
```

**Examples:**
- Set quantity to 50: `{"variant_id": "uuid", "quantity": 50, "adjust_delta": false}`
- Add 10 to current: `{"variant_id": "uuid", "quantity": 10, "adjust_delta": true}`
- Subtract 5: `{"variant_id": "uuid", "quantity": -5, "adjust_delta": true}`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Inventory adjusted successfully",
  "data": {
    "inventory": {
      "variant_id": "uuid",
      "quantity": 50,
      "low_stock_threshold": 10,
      "is_low_stock": false
    }
  }
}
```

### List Inventory

**Endpoint:** `GET /api/v1/admin/inventory`

**Query Parameters:**
- `page`, `per_page`: Pagination
- `low_stock_only`: Filter to low stock items
- `sku`: Search by SKU

---

## Order Management

### List Orders

**Endpoint:** `GET /api/v1/admin/orders`

**Query Parameters:**
- `page`, `per_page`: Pagination
- `status`: Filter by order status
- `user_id`: Filter by user
- `search`: Search in order details

### Update Order Status

**Endpoint:** `PATCH /api/v1/admin/orders/{order_id}/status`

**Request Body:**
```json
{
  "status": "SHIPPED",  // PENDING, PAID, PROCESSING, SHIPPED, DELIVERED, CANCELLED
  "notes": "Shipped via DHL"
}
```

---

## User Management

### List Users

**Endpoint:** `GET /api/v1/admin/users`

**Query Parameters:**
- `page`, `per_page`: Pagination
- `search`: Search by email/username
- `role`: Filter by role

### Assign Role

**Endpoint:** `POST /api/v1/admin/users/{user_id}/roles`

**Request Body:**
```json
{
  "role": "Customer"
}
```

### Revoke Role

**Endpoint:** `DELETE /api/v1/admin/users/{user_id}/roles`

**Request Body:**
```json
{
  "role": "Customer"
}
```

---

## Common Patterns

### Complete Product Creation Flow

```javascript
// Step 1: Create product (without variants)
const productResponse = await fetch('/api/v1/admin/products', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Kezura Mav Bone Straight Hair',
    category: 'Wigs',
    description: 'Premium hair extension',
    care: 'Detangle gently',
    details: '100% human hair',
    material_id: 'material-uuid',  // Optional - link to a pre-created material
    status: 'In-Stock'
    // SKU will be auto-generated as KZ-WG-XXXX
  })
});

const product = await productResponse.json();
const productId = product.data.product.id;

// Step 2: Create variants
const variant1 = await fetch(`/api/v1/admin/products/${productId}/variants`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    sku: 'KZ-WG-0A12-32BLK',
    price_ngn: 50000.00,
    price_usd: 50.00,
    attributes: {
      color: 'Black',
      length: '32',
      texture: 'Straight'
    }
  })
});

// Step 3: Update inventory
await fetch('/api/v1/admin/inventory/adjust', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    variant_id: variant1.data.variant.id,
    quantity: 10,
    adjust_delta: false
  })
});
```

### Handling Errors

```javascript
try {
  const response = await fetch('/api/v1/admin/products', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(productData)
  });

  if (!response.ok) {
    const error = await response.json();
    
    if (response.status === 401) {
      // Re-authenticate
      await clerk.signOut();
      window.location.href = '/login';
    } else if (response.status === 403) {
      // Show permission error
      alert('You do not have permission to perform this action');
    } else if (response.status === 409) {
      // Handle conflict (e.g., SKU exists)
      alert(`Conflict: ${error.message}`);
    } else {
      // Show generic error
      alert(`Error: ${error.message}`);
    }
    return;
  }

  const data = await response.json();
  // Handle success
} catch (error) {
  console.error('Network error:', error);
  alert('Network error. Please try again.');
}
```

### Color Field Explanation

**Important:** The `color` field is stored in variant `attributes`, not as a direct field.

- **When creating/updating a variant:** Set `attributes.color`
- **In response:** `color` is extracted from `attributes.color` for convenience
- **Product-level color:** Comma-separated list of all unique colors from variants

**Example:**
```json
// Request
{
  "attributes": {
    "color": "Black",  // ← Color goes here
    "length": "32"
  }
}

// Response
{
  "color": "Black",  // ← Extracted for convenience
  "attributes": {
    "color": "Black",  // ← Original location
    "length": "32"
  }
}
```

---

## Response Field Reference

### Product Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Product ID |
| `name` | string | Product name |
| `sku` | string | Product SKU (format: KZ-XX-XXXX) |
| `slug` | string | URL-friendly slug |
| `description` | string | Product description |
| `category` | string | Product category |
| `care` | string | Care instructions |
| `details` | string | Product details |
| `material` | string | Product material |
| `status` | string | Product status (alias for launch_status) |
| `price_ngn` | number | Minimum price in NGN (from variants) |
| `price_usd` | number | Minimum price in USD (from variants) |
| `price` | number | Alias for price_ngn |
| `color` | string | Comma-separated colors from variants |
| `stock` | number | Total stock from all variants |
| `variants` | array | Array of variant objects |

### Variant Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Variant ID |
| `sku` | string | Variant SKU |
| `price_ngn` | number | Price in NGN |
| `price_usd` | number | Price in USD (optional) |
| `price` | number | Alias for price_ngn |
| `color` | string | Extracted from attributes.color |
| `stock` | number | Stock quantity (alias for stock_quantity) |
| `stock_quantity` | number | Stock quantity |
| `attributes` | object | Variant attributes (color, length, texture, etc.) |
| `is_in_stock` | boolean | Whether variant is in stock |
| `inventory` | object | Full inventory details (if requested) |

---

## Best Practices

1. **Always include error handling** for network and API errors
2. **Handle 401 errors** by re-authenticating the user
3. **Validate data** on the frontend before sending to API
4. **Use pagination** for large lists (don't fetch all at once)
5. **Cache product data** when appropriate to reduce API calls
6. **Show loading states** during API calls
7. **Confirm destructive actions** (delete, etc.) before executing
8. **Handle SKU conflicts** gracefully (suggest alternative SKU)
9. **Update inventory** after creating variants
10. **Use status field** instead of launch_status for consistency

---

## Support

For API issues or questions:
- Check error messages in response
- Verify authentication token is valid
- Ensure user has required role
- Review request body matches schema
- Check server logs for detailed errors

