# UVTAB Informal System - SchoolPay API Documentation

**Version:** 2.0  
**Last Updated:** February 2025  
**Contact:** cagaba@uvtab.go.ug  
**Institution:** Uganda Vocational and Technical Assessment Board (UVTAB)

---

## Overview

This document provides the technical specifications for integrating SchoolPay with the UVTAB Informal Assessment System. The integration enables candidates to pay their assessment fees through SchoolPay payment channels.

---

## Base URL

| Environment | Base URL |
|-------------|----------|
| **Production** | `https://emis.uvtab.go.ug/api/candidates/payments/schoolpay` |
| **Staging/Testing** | `https://staging-emis.uvtab.go.ug/api/candidates/payments/schoolpay` |

> **Important:** Use the **Staging** environment for all integration testing. The Production environment has live candidate data and should only be used after successful staging tests.

---

## Authentication

All API requests require authentication using an API key.

### API Key Header

```
X-API-Key: <your-api-key>
```

**Alternative Methods:**
```
Authorization: Bearer <your-api-key>
```

### IP Whitelisting

For security, only requests from whitelisted SchoolPay server IPs will be accepted. Please provide your server IP addresses during integration setup.

---

## Payment Code Format

| Component | Description | Example |
|-----------|-------------|---------|
| Prefix | Always `IUV` | IUV |
| Center Code | 3 digits | 002 |
| Year | 2 digits | 25 |
| Candidate ID | 6 digits | 000001 |
| **Full Code** | **14 characters** | **IUV00225000001** |

---

## API Endpoints

### 1. Check Balance

Retrieve candidate billing information before processing payment.

**Endpoint:** `POST /check-balance/`

**Request Headers:**
```
Content-Type: application/json
X-API-Key: <your-api-key>
```

**Request Body:**
```json
{
    "payment_code": "IUV00225000001"
}
```

**Success Response (200 OK):**
```json
{
    "success": true,
    "student_no": "IUV00225000001",
    "student_name": "John Doe",
    "registration_number": "UVT002/U/25/A/HD/F/0001",
    "school_name": "Assessment Center Name",
    "outstanding_balance": 80000.00,
    "total_billed": 80000.00,
    "amount_paid": 0.00,
    "currency": "UGX",
    "payment_cleared": false
}
```

**Error Response - Candidate Not Found (404):**
```json
{
    "success": false,
    "error": "Candidate not found",
    "message": "No candidate found with this payment code. Please contact your Institution."
}
```

**Error Response - Missing Payment Code (400):**
```json
{
    "success": false,
    "error": "Missing payment_code",
    "message": "Payment code is required"
}
```

---

### 2. Payment Callback

Notify the system when a payment is completed. This endpoint should be called by SchoolPay after a successful payment.

**Endpoint:** `POST /callback/`

**Request Headers:**
```
Content-Type: application/json
X-API-Key: <your-api-key>
```

**Request Body:**
```json
{
    "payment_code": "IUV00225000001",
    "school_pay_reference": "37414523724",
    "amount": 80000.00,
    "payment_status": "Pending Approval",
    "attempt_status": "Successful",
    "payment_date": "2025-01-12T14:30:00",
    "phone_number": "256700000000",
    "channel": "MTN Mobile Money"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payment_code` | String | Yes | Candidate's payment code (14 characters) |
| `school_pay_reference` | String | Yes | SchoolPay transaction reference |
| `amount` | Decimal | Yes | Amount paid in UGX |
| `payment_status` | String | Yes | Payment status from SchoolPay |
| `attempt_status` | String | Yes | "Successful" or "Failed" |
| `payment_date` | DateTime | Yes | ISO 8601 format |
| `phone_number` | String | No | Payer's phone number |
| `channel` | String | No | Payment channel (MTN, Airtel, etc.) |

**Success Response (200 OK):**
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

**Error Response - Partial Payment Rejected (400):**
```json
{
    "success": false,
    "error": "Partial payment not allowed",
    "message": "Payment amount must be exactly UGX 80000.0. Partial payments are not accepted.",
    "amount_paid": 40000.00,
    "required_amount": 80000.00
}
```

**Error Response - Candidate Not Found (404):**
```json
{
    "success": false,
    "error": "Candidate not found",
    "message": "No candidate found with this payment code"
}
```

---

### 3. Test Connection

Verify connectivity between SchoolPay and UBTEB API.

**Endpoint:** `GET /test/`

**Request Headers:**
```
X-API-Key: <your-api-key>
```

**Success Response (200 OK):**
```json
{
    "success": true,
    "message": "Connection successful",
    "system": "UVTAB Informal System",
    "version": "1.0"
}
```

---

## Error Codes

| HTTP Code | Error | Description |
|-----------|-------|-------------|
| 200 | - | Success |
| 400 | Bad Request | Missing or invalid parameters |
| 401 | Unauthorized | Invalid or missing API key |
| 403 | Forbidden | IP address not whitelisted |
| 404 | Not Found | Candidate not found |
| 500 | Server Error | Internal server error |

### Authentication Errors

**Invalid API Key (401):**
```json
{
    "success": false,
    "error": "Unauthorized",
    "message": "Invalid or missing API key"
}
```

**IP Not Whitelisted (403):**
```json
{
    "success": false,
    "error": "Forbidden",
    "message": "Access denied from your IP address"
}
```

---

## Integration Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Candidate  │         │  SchoolPay   │         │  UBTEB API  │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                        │
      │ 1. Enter Payment Code  │                        │
      │───────────────────────>│                        │
      │                        │                        │
      │                        │ 2. POST /check-balance │
      │                        │───────────────────────>│
      │                        │                        │
      │                        │ 3. Return Balance      │
      │                        │<───────────────────────│
      │                        │                        │
      │ 4. Display Balance     │                        │
      │<───────────────────────│                        │
      │                        │                        │
      │ 5. Confirm & Pay       │                        │
      │───────────────────────>│                        │
      │                        │                        │
      │                        │ 6. POST /callback      │
      │                        │───────────────────────>│
      │                        │                        │
      │                        │ 7. Confirmation        │
      │                        │<───────────────────────│
      │                        │                        │
      │ 8. Payment Receipt     │                        │
      │<───────────────────────│                        │
```

---

## Important Business Rules

### 1. No Partial Payments
- Candidates **must pay the full outstanding balance**
- Partial payments will be **rejected**
- The exact `outstanding_balance` amount must be paid

### 2. Currency
- All amounts are in **UGX (Ugandan Shillings)**
- No currency conversion is required

### 3. Payment Validation
- Only payments with `attempt_status: "Successful"` are processed
- Failed attempts are logged but not applied to candidate balance

---

## Sample Integration Code

### Check Balance (cURL)
```bash
curl -X POST https://staging-emis.uvtab.go.ug/api/candidates/payments/schoolpay/check-balance/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{"payment_code": "IUV00225000001"}'
```

### Payment Callback (cURL)
```bash
curl -X POST https://staging-emis.uvtab.go.ug/api/candidates/payments/schoolpay/callback/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "payment_code": "IUV00225000001",
    "school_pay_reference": "37414523724",
    "amount": 80000.00,
    "payment_status": "Pending Approval",
    "attempt_status": "Successful",
    "payment_date": "2025-01-12T14:30:00",
    "phone_number": "256700000000",
    "channel": "MTN Mobile Money"
  }'
```

### Test Connection (cURL)
```bash
curl -X GET https://staging-emis.uvtab.go.ug/api/candidates/payments/schoolpay/test/ \
  -H "X-API-Key: <your-api-key>"
```

---

## Integration Checklist

### Information We Need From SchoolPay:
- [ ] SchoolPay server IP addresses (for IP whitelisting on our side)
- [ ] Callback retry policy (if initial callback fails, how many retries and at what interval?)
- [ ] Technical support contact for integration issues

### Information We Provide to SchoolPay:
- [x] API endpoints (documented above)
- [x] Request/response formats (documented above)
- [x] Payment code format: `IUV[center][year][candidateID]` (14 characters)
- [x] Currency: UGX (Ugandan Shillings)
- [x] Institution: **UVTAB - Informal Assessment System**
- [x] Production URL: `https://emis.uvtab.go.ug/api/candidates/payments/schoolpay`
- [x] Staging/Test URL: `https://staging-emis.uvtab.go.ug/api/candidates/payments/schoolpay`
- [x] API Key: *(shared securely via separate channel)*
- [x] Business rule: **No partial payments** — full amount only

---

## Testing

### Test Scenarios to Verify:

| Scenario | Expected Result |
|----------|-----------------|
| Valid payment code | Returns candidate details and balance |
| Invalid payment code | Returns 404 with error message |
| Missing payment code | Returns 400 with error message |
| Full payment callback | Payment recorded, `payment_cleared: true` |
| Partial payment callback | Returns 400, payment rejected |
| Invalid API key | Returns 401 Unauthorized |
| Unauthorized IP | Returns 403 Forbidden |

---

## Environments

### Production
- **URL:** `https://emis.uvtab.go.ug/api/candidates/payments/schoolpay`
- **Data:** Live candidate registrations — do NOT use for testing
- **API Key:** Same key works on both environments

### Staging (for testing)
- **URL:** `https://staging-emis.uvtab.go.ug/api/candidates/payments/schoolpay`
- **Data:** Test candidates pre-loaded for integration testing
- **Purpose:** Verify check-balance, callback, error handling before going live

### Test Payment Codes (Staging Only)

| Payment Code | Candidate Name | Balance (UGX) | Notes |
|-------------|----------------|---------------|-------|
| `IUV99925000001` | Test Candidate One | 80,000 | Standard test candidate |
| `IUV99925000002` | Test Candidate Two | 120,000 | Higher balance test |
| `IUV99925000003` | Test Candidate Three | 0 | Already paid / zero balance |

---

## Support

**Technical Contact:**  
Name: Claire Agaba  
Email: cagaba@uvtab.go.ug  
Organization: UVTAB - Uganda Vocational and Technical Assessment Board

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | January 2025 | Initial release |
| 2.0 | February 2025 | Added production & staging URLs, test payment codes, updated checklist |
