# SchoolPay Integration Setup Guide

## Quick Start

This guide will help you set up the SchoolPay integration with security features enabled.

## Step 1: Configure Environment Variables

Add these variables to your `.env` file:

```bash
# SchoolPay Integration Security
SCHOOLPAY_ENABLED=True
SCHOOLPAY_API_KEY=your-secret-api-key-from-schoolpay
SCHOOLPAY_ALLOWED_IPS=41.210.142.199,41.210.142.200
```

### Getting the Values:

**SCHOOLPAY_ENABLED:**
- Set to `False` during development/testing (disables security checks)
- Set to `True` in production (enables API key and IP validation)

**SCHOOLPAY_API_KEY:**
- Request this from SchoolPay during integration setup
- Keep it secret and secure
- Never commit it to version control
- Example: `sk_live_abc123xyz789`

**SCHOOLPAY_ALLOWED_IPS:**
- Request SchoolPay's server IP addresses
- Multiple IPs separated by commas (no spaces)
- Example: `41.210.142.199,41.210.142.200,41.210.142.201`

## Step 2: Verify Settings Configuration

The settings are already configured in `backend/emis/settings.py`:

```python
# SchoolPay Integration Settings
SCHOOLPAY_API_KEY = config('SCHOOLPAY_API_KEY', default='')
SCHOOLPAY_ALLOWED_IPS = config('SCHOOLPAY_ALLOWED_IPS', default='', cast=Csv())
SCHOOLPAY_ENABLED = config('SCHOOLPAY_ENABLED', default=False, cast=bool)
```

## Step 3: Verify Middleware is Active

Check that the middleware is in `MIDDLEWARE` list in `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware ...
    'candidates.middleware.SchoolPaySecurityMiddleware',  # SchoolPay API security
]
```

## Step 4: Test the Setup

### Test 1: Without Security (Development)

Set in `.env`:
```bash
SCHOOLPAY_ENABLED=False
```

Test:
```bash
curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/check-balance/ \
  -H "Content-Type: application/json" \
  -d '{"payment_code": "IUV00225000001"}'
```

Expected: Should work without API key or IP validation

### Test 2: With Security (Production)

Set in `.env`:
```bash
SCHOOLPAY_ENABLED=True
SCHOOLPAY_API_KEY=test-key-123
SCHOOLPAY_ALLOWED_IPS=127.0.0.1,::1
```

Test without API key:
```bash
curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/check-balance/ \
  -H "Content-Type: application/json" \
  -d '{"payment_code": "IUV00225000001"}'
```

Expected: `401 Unauthorized - Invalid or missing API key`

Test with API key:
```bash
curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/check-balance/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-123" \
  -d '{"payment_code": "IUV00225000001"}'
```

Expected: Should work and return candidate balance

## Step 5: Share Information with SchoolPay

Provide SchoolPay with:

### 1. API Endpoints:
```
Check Balance: https://yourdomain.com/api/candidates/payments/schoolpay/check-balance/
Payment Callback: https://yourdomain.com/api/candidates/payments/schoolpay/callback/
Test Connection: https://yourdomain.com/api/candidates/payments/schoolpay/test/
```

### 2. Authentication Method:
```
Method: API Key in Header
Header Name: X-API-Key
Header Value: [Your API Key]

Alternative: Authorization: Bearer [Your API Key]
```

### 3. Request Format:
```json
{
    "payment_code": "IUV00225000001"
}
```

### 4. Response Format:
```json
{
    "success": true,
    "student_no": "IUV00225000001",
    "student_name": "John Doe",
    "school_name": "UVTAB - Informal System",
    "outstanding_balance": 80000.00,
    "currency": "UGX"
}
```

## Step 6: Request Information from SchoolPay

Ask SchoolPay for:

1. **API Key** - For authentication
2. **Server IP Addresses** - For IP whitelisting
3. **Callback Format** - Exact fields they will send
4. **Test Environment** - Sandbox URLs for testing
5. **Support Contact** - Technical support person

## Security Features

### 1. API Key Authentication
- Validates API key on every request
- Supports multiple header formats
- Returns 401 if key is invalid or missing

### 2. IP Whitelisting
- Only allows requests from configured IPs
- Returns 403 if IP is not whitelisted
- Handles proxy headers (X-Forwarded-For, X-Real-IP)

### 3. Logging
- All authentication attempts are logged
- Failed attempts include IP address
- Successful requests are logged for audit

### 4. Flexible Configuration
- Can disable security for development
- Can enable/disable features independently
- Environment-based configuration

## Troubleshooting

### Issue: "Invalid or missing API key"

**Cause:** API key not sent or incorrect

**Solution:**
1. Check `.env` file has correct `SCHOOLPAY_API_KEY`
2. Verify header is sent: `X-API-Key: your-key`
3. Check logs: `tail -f /var/log/django/debug.log`

### Issue: "Access denied from your IP address"

**Cause:** Client IP not in whitelist

**Solution:**
1. Check `.env` file has correct `SCHOOLPAY_ALLOWED_IPS`
2. Verify SchoolPay's actual IP address
3. Check if behind proxy (may need X-Forwarded-For)
4. Temporarily disable IP check for testing:
   ```bash
   SCHOOLPAY_ALLOWED_IPS=
   ```

### Issue: Security not working (no validation)

**Cause:** `SCHOOLPAY_ENABLED=False` or not set

**Solution:**
1. Set `SCHOOLPAY_ENABLED=True` in `.env`
2. Restart Django server
3. Test with invalid key to verify

### Issue: Works locally but not in production

**Cause:** Environment variables not set in production

**Solution:**
1. Check production `.env` file exists
2. Verify variables are loaded: `python manage.py shell`
   ```python
   from django.conf import settings
   print(settings.SCHOOLPAY_ENABLED)
   print(settings.SCHOOLPAY_API_KEY)
   print(settings.SCHOOLPAY_ALLOWED_IPS)
   ```
3. Restart production server

## Production Checklist

Before going live:

- [ ] `SCHOOLPAY_ENABLED=True` in production `.env`
- [ ] Valid API key from SchoolPay configured
- [ ] SchoolPay server IPs added to whitelist
- [ ] Test endpoints with valid API key
- [ ] Test endpoints with invalid API key (should fail)
- [ ] Test from unauthorized IP (should fail)
- [ ] Verify logging is working
- [ ] Share production URLs with SchoolPay
- [ ] Confirm SchoolPay can access endpoints
- [ ] Test full payment flow end-to-end
- [ ] Monitor logs for first real payments

## Monitoring

### Check Logs:
```bash
# View authentication logs
grep "SchoolPay API" /var/log/django/debug.log

# View failed attempts
grep "SchoolPay API: Invalid" /var/log/django/debug.log

# View successful requests
grep "SchoolPay API: Authenticated" /var/log/django/debug.log
```

### Monitor Payments:
```bash
# Check recent payments
python manage.py shell
>>> from candidates.models import Candidate
>>> Candidate.objects.filter(payment_cleared=True).order_by('-payment_cleared_date')[:10]
```

## Support

For issues with this integration:
- Technical: UVTAB Technical Team
- Email: cagaba@uvtab.go.ug
- Documentation: See `SCHOOLPAY_INTEGRATION.md`
