# SchoolPay Integration Documentation

## Overview
This document outlines the integration between UVTAB Informal System and SchoolPay payment gateway.

## Integration Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Candidate  │────────▶│  SchoolPay   │────────▶│ UBTEB API   │
│             │         │   Portal     │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                        │
      │ 1. Enter Payment Code  │                        │
      │───────────────────────▶│                        │
      │                        │                        │
      │                        │ 2. Check Balance       │
      │                        │───────────────────────▶│
      │                        │                        │
      │                        │ 3. Return Balance Info │
      │                        │◀───────────────────────│
      │                        │                        │
      │ 4. Enter Amount & Pay  │                        │
      │───────────────────────▶│                        │
      │                        │                        │
      │                        │ 5. Payment Callback    │
      │                        │───────────────────────▶│
      │                        │                        │
      │                        │ 6. Confirmation        │
      │                        │◀───────────────────────│
      │                        │                        │
      │ 7. Payment Receipt     │                        │
      │◀───────────────────────│                        │
```

## API Endpoints

### 1. Check Balance Endpoint

**Purpose:** SchoolPay queries this endpoint to get candidate billing information

**Endpoint:** `GET/POST /api/candidates/payments/schoolpay/check-balance/`

**Request from SchoolPay:**
```json
{
    "payment_code": "IUV00225000001"
}
```

**Response to SchoolPay:**
```json
{
    "success": true,
    "student_no": "IUV00225000001",
    "student_name": "John Doe",
    "registration_number": "UVT002/U/25/A/HD/F/0001",
    "school_name": "Test Center2",
    "outstanding_balance": 80000.00,
    "total_billed": 80000.00,
    "amount_paid": 0.00,
    "currency": "UGX",
    "payment_cleared": false
}
```

**Note:** `school_name` is dynamically retrieved from the candidate's assessment center.

**Error Response (Candidate Not Found):**
```json
{
    "success": false,
    "error": "Candidate not found",
    "message": "No candidate found with this payment code. Please contact your Instituition."
}
```

### 2. Payment Callback Endpoint

**Purpose:** SchoolPay notifies us when a payment is made

**Endpoint:** `POST /api/candidates/payments/schoolpay/callback/`

**Request from SchoolPay:**
```json
{
    "payment_code": "IUV00225000001",
    "school_pay_reference": "37414523724",
    "amount": 80000.00,
    "payment_status": "Pending Approval",
    "attempt_status": "Successful",
    "payment_date": "2025-12-23T13:55:23",
    "phone_number": "256700000000",
    "channel": "MTN Mobile Money"
}
```

**Response to SchoolPay (Success):**
```json
{
    "success": true,
    "message": "Payment recorded successfully",
    "transaction_id": "37414523724",
    "candidate_name": "John Doe",
    "amount_paid": 80000.00,
    "total_paid": 80000.00,
    "payment_cleared": true
}
```

**Response to SchoolPay (Partial Payment Rejected):**
```json
{
    "success": false,
    "error": "Partial payment not allowed",
    "message": "Payment amount must be exactly UGX 80000.0. Partial payments are not accepted.",
    "amount_paid": 40000.00,
    "required_amount": 80000.00
}
```

### 3. Test Connection Endpoint

**Purpose:** Verify connectivity between SchoolPay and UVTAB API

**Endpoint:** `GET /api/candidates/payments/schoolpay/test/`

**Response:**
```json
{
    "success": true,
    "message": "Connection successful",
    "system": "UVTAB Informal System",
    "version": "1.0"
}
```

## Information Exchange

### What UVTAB Provides to SchoolPay:

1. **Payment Code** - Unique identifier (e.g., `IUV001250000001`)
2. **Student Name** - Full name of the candidate
3. **Registration Number** - Candidate's registration number
4. **School Name** - Candidate's assessment center name (e.g., "UVTAB Institution")
5. **Outstanding Balance** - Amount owed in UGX
6. **Total Billed** - Total amount billed across all enrollments


### What SchoolPay Provides to UVTAB:

1. **School Pay Reference** - Unique transaction ID (e.g., `37414523724`)
2. **Amount** - Amount paid in UGX
3. **Payment Status** - "Pending Approval", "Not Paid", etc.
4. **Attempt Status** - "Successful", "No Attempt", etc.
5. **Payment Date** - Timestamp of payment
6. **Phone Number** - Payer's phone number
7. **Channel** - Payment method (MTN Mobile Money, Airtel Money, etc.)

## Payment Logic


### Payment Clearing Logic:
1. When payment callback is received with `attempt_status = "Successful"`
2. **Validate payment amount matches total billed exactly**
3. If amount doesn't match, reject payment with error
4. If amount matches, set `payment_amount_cleared = payment_amount`
5. Mark `payment_cleared = True`
6. Store SchoolPay reference in `payment_center_series_ref`

### ⚠️ IMPORTANT: No Partial Payments
- **Partial payments are NOT allowed**
- Candidate must pay the full outstanding balance
- If payment amount ≠ total billed, payment is rejected
- Error returned: "Payment amount must be exactly UGX [amount]. Partial payments are not accepted."

## Security Considerations

### API Access:
- Endpoints use `AllowAny` permission (SchoolPay access without user authentication)
- SchoolPay will access these endpoints directly
- ✅ **IP whitelisting implemented** - Only allowed IPs can access
- ✅ **API key authentication implemented** - Validates API key on each request

### Security Implementation:

#### 1. Environment Variables (`.env` file):
```bash
# SchoolPay Integration Security
SCHOOLPAY_ENABLED=True  # Set to True to enable security checks
SCHOOLPAY_API_KEY=your-secret-api-key-from-schoolpay
SCHOOLPAY_ALLOWED_IPS=41.210.142.199,41.210.142.200  # SchoolPay server IPs (comma-separated)
```

#### 2. Settings Configuration (`settings.py`):
```python
# SchoolPay Integration Settings
SCHOOLPAY_API_KEY = config('SCHOOLPAY_API_KEY', default='')
SCHOOLPAY_ALLOWED_IPS = config('SCHOOLPAY_ALLOWED_IPS', default='', cast=Csv())
SCHOOLPAY_ENABLED = config('SCHOOLPAY_ENABLED', default=False, cast=bool)
```

#### 3. Middleware (`candidates/middleware.py`):
- Validates API key from request headers
- Validates client IP address against whitelist
- Logs all authentication attempts
- Returns 401 for invalid API key
- Returns 403 for unauthorized IP

#### 4. API Key Header Options:
SchoolPay can send the API key in any of these ways:
```bash
# Option 1: X-API-Key header (Recommended)
X-API-Key: your-secret-api-key

# Option 2: Authorization Bearer token
Authorization: Bearer your-secret-api-key

# Option 3: Query parameter (Fallback)
?api_key=your-secret-api-key
```

## Testing

### Test Scenarios:

1. **Check Balance - Candidate Exists:**
   ```bash
   curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/check-balance/ \
     -H "Content-Type: application/json" \
     -d '{"payment_code": "IUV00225000001"}'
   ```

2. **Check Balance - Candidate Not Found:**
   ```bash
   curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/check-balance/ \
     -H "Content-Type: application/json" \
     -d '{"payment_code": "INVALID123"}'
   ```

3. **Payment Callback - Successful:**
   ```bash
   curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/callback/ \
     -H "Content-Type: application/json" \
     -d '{
       "payment_code": "IUV00225000001",
       "school_pay_reference": "37414523724",
       "amount": 80000.00,
       "payment_status": "Pending Approval",
       "attempt_status": "Successful",
       "payment_date": "2025-12-23T13:55:23",
       "phone_number": "256700000000",
       "channel": "MTN Mobile Money"
     }'
   ```

4. **Test Connection:**
   ```bash
   curl http://localhost:8000/api/candidates/payments/schoolpay/test/
   ```

### Security Testing:

1. **Test with Valid API Key:**
   ```bash
   curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/check-balance/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-secret-api-key" \
     -d '{"payment_code": "IUV00225000001"}'
   ```

2. **Test with Invalid API Key (Should return 401):**
   ```bash
   curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/check-balance/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: wrong-key" \
     -d '{"payment_code": "IUV00225000001"}'
   ```

3. **Test with Bearer Token:**
   ```bash
   curl -X POST http://localhost:8000/api/candidates/payments/schoolpay/check-balance/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-secret-api-key" \
     -d '{"payment_code": "IUV00225000001"}'
   ```

4. **Test from Unauthorized IP (Should return 403):**
   - Access from IP not in `SCHOOLPAY_ALLOWED_IPS`
   - Should receive: `{"success": false, "error": "Forbidden", "message": "Access denied from your IP address"}`

## Configuration Steps for SchoolPay

### Information to Provide to SchoolPay:

1. **School/Institution Details:**
   - Name: UBTEB - Informal System
   - Institution Code: (To be assigned by SchoolPay)

2. **API Endpoints:**
   - Check Balance URL: `https://yourdomain.com/api/candidates/payments/schoolpay/check-balance/`
   - Payment Callback URL: `https://yourdomain.com/api/candidates/payments/schoolpay/callback/`
   - Test URL: `https://yourdomain.com/api/candidates/payments/schoolpay/test/`

3. **Payment Code Format:**
   - Format: `IUV[center][year][candidateID]`
   - Example: `IUV00225000001`
   - Length: 14 characters
   - Prefix: Always starts with "IUV"

4. **Currency:**
   - UGX (Ugandan Shillings)

5. **Payment Types:**
   - Assessment fees
   - Enrollment fees

### Information to Request from SchoolPay:

1. **API Documentation:**
   - Exact request/response formats
   - Required headers
   - Authentication method (if any)

2. **Callback Specifications:**
   - Exact field names they will send
   - Possible values for `payment_status`
   - Possible values for `attempt_status`
   - Retry logic for failed callbacks

3. **Testing Environment:**
   - Sandbox/test API URLs
   - Test payment codes
   - Test credentials

4. **IP Addresses:**
   - List of SchoolPay server IPs for whitelisting

5. **Support Contact:**
   - Technical support email/phone
   - Integration support person

## Monitoring & Logging

### What to Monitor:
1. Failed balance check requests
2. Payment callbacks with failed attempts
3. Mismatched payment amounts
4. Duplicate payment references

### Logging:
- All payment callbacks are logged with `logger.info()`
- Errors are logged with `logger.error()`
- Check logs at: `/var/log/django/` or Django admin logs

## Troubleshooting

### Common Issues:

1. **"No candidate invoice set"**
   - Candidate doesn't have any enrollments
   - Solution: Ensure candidate is enrolled in at least one assessment series

2. **Payment not reflecting**
   - Check if callback was received (check logs)
   - Verify payment reference in database
   - Check if `attempt_status` was "Successful"

3. **Wrong outstanding balance**
   - Verify enrollment amounts are correct
   - Check `payment_amount_cleared` field
   - Recalculate: Total Billed - Amount Paid

## Next Steps

1. ✅ API endpoints created
2. ⏳ Contact SchoolPay for integration details
3. ⏳ Set up test environment
4. ⏳ Test with sample payment codes
5. ⏳ Add IP whitelisting (optional)
6. ⏳ Add API key authentication (optional)
7. ⏳ Deploy to production
8. ⏳ Monitor first real payments

## Support

For technical issues with this integration:
- Check logs: `python manage.py check_payment_logs`
- Contact: UVTAB Technical Team
- Email:cagaba@uvtab.go.ug
