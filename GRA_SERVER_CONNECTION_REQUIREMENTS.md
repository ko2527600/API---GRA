# GRA Server Connection Requirements

## What You Need to Connect to GRA Server

To connect your system to the actual GRA (Ghana Revenue Authority) E-VAT server, you need the following:

---

## 1. GRA API Configuration (Environment Variables)

### Required in `.env` file:

```env
# GRA API Base URL
GRA_API_BASE_URL=https://apitest.e-vatgh.com/evat_apiqa

# API Timeout (seconds)
GRA_API_TIMEOUT=30

# Retry Configuration
GRA_API_RETRIES=5
MAX_RETRIES=5
RETRY_BACKOFF_BASE=1
RETRY_BACKOFF_MAX=3600
```

### Current Status:
✅ Already configured in your `.env`:
```
GRA_API_BASE_URL=https://apitest.e-vatgh.com/evat_apiqa
GRA_API_TIMEOUT=30
GRA_API_RETRIES=5
```

---

## 