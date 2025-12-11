# Environment Variables

This document lists all environment variables required for the House of Kezura BFF.

## Required Variables

### Database
- `DATABASE_URL` - PostgreSQL connection string (e.g., `postgresql://user:pass@localhost/kezura`)

### Authentication (Clerk)
- `CLERK_SECRET_KEY` - Clerk backend API secret key (required)
- `CLERK_PUBLISHABLE_KEY` - Clerk publishable key for frontend
- `CLERK_FRONTEND_API` - Clerk frontend API key
- `CLERK_BACKEND_API` - Clerk backend API URL (default: `https://api.clerk.com/v1`)

### Application
- `SECRET_KEY` - Flask secret key for session management
- `ENV` - Environment name: `development`, `production`, or `testing` (default: `development`)
- `DEBUG` - Enable debug mode (auto-set based on ENV)

### Guest Account Auto-Creation
- `DEFAULT_GUEST_PREFIX` - Prefix for auto-generated guest passwords (default: `kezura`)
  - Format: `{DEFAULT_GUEST_PREFIX}_{random_16_chars}`
  - Example: `kezura_aB3xY9mN2pQ7rT5v`

### CORS
- `CLIENT_ORIGINS` - Comma-separated list of allowed origins (default: `http://localhost:3000,http://localhost:5173`)

### Email (Flask-Mail)
- `MAIL_SERVER` - SMTP server (default: `smtp.gmail.com`)
- `MAIL_PORT` - SMTP port (default: `587`)
- `MAIL_USERNAME` - SMTP username
- `MAIL_PASSWORD` - SMTP password
- `MAIL_DEFAULT_SENDER` - Default sender email address

### Cloudinary (Media Storage)
- `CLOUDINARY_CLOUD_NAME` - Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Cloudinary API key
- `CLOUDINARY_API_SECRET` - Cloudinary API secret

### Payment Gateway
- `PAYMENT_GATEWAY` - Payment gateway name (e.g., `flutterwave`, `paystack`, `stripe`)
- `PAYMENT_GATEWAY_API_KEY` - Payment gateway API key
- `PAYMENT_GATEWAY_SECRET_KEY` - Payment gateway secret key
- `PAYMENT_GATEWAY_PUBLIC_KEY` - Payment gateway public key
- `PAYMENT_GATEWAY_TEST_MODE` - Enable test mode (optional)
- `PAYMENT_GATEWAY_TEST_API_KEY` - Test API key (optional)
- `PAYMENT_GATEWAY_TEST_SECRET_KEY` - Test secret key (optional)
- `PAYMENT_GATEWAY_TEST_PUBLIC_KEY` - Test public key (optional)

### Exchange Rate API
- `EXCHANGE_RATE_API_KEY` - ExchangeRate-API key for currency conversion

### Currency
- `CURRENCY_MARKUP_PERCENTAGE` - Optional markup percentage (default: `0.0`)
- `DEFAULT_CURRENCY` - Default currency code (default: `NGN`)

### Domains
- `APP_DOMAIN` - Frontend application domain (default: `http://localhost:3000`)
- `API_DOMAIN` - Backend API domain (default: `http://localhost:5050`)

### Logging
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `BASE_LOG_LEVEL` - Base logging level (default: `WARNING`)

### Database Seeding
- `SEED_DB` - Enable database seeding on startup (default: `False`)
- `DEFAULT_ADMIN_USERNAME` - Default admin username for seeding
- `DEFAULT_ADMIN_PASSWORD` - Default admin password for seeding

### Legacy (Deprecated)
- `JWT_SECRET_KEY` - Legacy JWT secret (deprecated, using Clerk)

## Example `.env` File

```env
# Environment
ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/kezura

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_xxxxx
CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_FRONTEND_API=pk_test_xxxxx

# Guest Account Auto-Creation
DEFAULT_GUEST_PREFIX=kezura

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@kezura.com

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Payment Gateway
PAYMENT_GATEWAY=flutterwave
PAYMENT_GATEWAY_API_KEY=your-api-key
PAYMENT_GATEWAY_SECRET_KEY=your-secret-key
PAYMENT_GATEWAY_PUBLIC_KEY=your-public-key

# Exchange Rate
EXCHANGE_RATE_API_KEY=your-api-key

# CORS
CLIENT_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Notes

- All environment variables are optional except `DATABASE_URL` and `CLERK_SECRET_KEY` for production
- Default values are provided where applicable
- The `DEFAULT_GUEST_PREFIX` is used to generate secure random passwords for auto-created guest accounts
- Idempotency keys in checkout are stored in cache (24-hour TTL) to prevent duplicate orders




