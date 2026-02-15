# External Integration API Design for GRA Invoice Submission

## 1. Introduction

This document outlines the design for an external API that allows registered businesses to securely submit their invoices to the Ghana Revenue Authority (GRA) system for verification. This API will act as an intermediary, simplifying the submission process for businesses by abstracting the complexities of the underlying GRA E-VAT API and its specific data requirements, such as the custom levy field mapping.

## 2. API Scope and Purpose

The primary purpose of this API is to provide a streamlined and secure interface for external business systems (e.g., ERPs, accounting software) to integrate with the GRA ERP Integration Platform. It will handle authentication, data transformation, and submission to the GRA E-VAT API, as well as provide mechanisms for status tracking and notifications.

## 3. Authentication

To ensure secure access and tenant isolation, businesses will authenticate with the External Integration API using an **API Key and API Secret** pair. These credentials will be generated and managed within the existing GRA ERP Integration Platform's business dashboard. The API Key will identify the business, and the API Secret will be used to sign requests, ensuring authenticity and integrity.

**Mechanism:**
*   **API Key (Header):** `X-API-Key: <your_api_key>`
*   **API Secret (Request Signature):** A signature generated using the API Secret and request payload will be included in a header (e.g., `X-API-Signature`). The backend will verify this signature against the stored API Secret for the given API Key.

## 4. API Endpoints

### 4.1. Submit Invoice

This endpoint allows businesses to submit their invoice data. The API will then transform this data into the GRA E-VAT API format, including handling the custom levy mapping, and queue it for submission to the GRA.

*   **Endpoint:** `POST /api/v1/external/invoices`
*   **Description:** Submits a new invoice for GRA verification.
*   **Authentication:** API Key and Signature.
*   **Request Body (JSON Example):**

```json
{
  "invoice_number": "BIZ-INV-2026-001",
  "customer_name": "Customer Name Ltd",
  "customer_tin": "P0000123456",
  "transaction_date": "2026-02-10",
  "transaction_type": "INVOICE",
  "sale_type": "NORMAL",
  "items": [
    {
      "item_code": "PROD-XYZ",
      "description": "Product Description",
      "quantity": 5,
      "unit_price": 200.00,
      "discount": 10.00
    }
  ],
  "base_amount": 990.00, 
  "total_vat": 148.50, 
  "total_levy": 49.50, 
  "total_amount": 1188.00, 
  "erp_reference_id": "ERP-REF-456"
}
```

*   **Response (202 Accepted - JSON Example):**

```json
{
  "submission_id": "uuid_of_submission",
  "status": "RECEIVED",
  "message": "Invoice received and queued for processing."
}
```

### 4.2. Get Invoice Submission Status

This endpoint allows businesses to retrieve the current status of a previously submitted invoice.

*   **Endpoint:** `GET /api/v1/external/invoices/{submission_id}/status`
*   **Description:** Retrieves the status of a specific invoice submission.
*   **Authentication:** API Key and Signature.
*   **Response (200 OK - JSON Example):**

```json
{
  "submission_id": "uuid_of_submission",
  "invoice_number": "BIZ-INV-2026-001",
  "status": "SUCCESS", 
  "gra_invoice_id": "GRA-INV-2026-001", 
  "gra_qr_code": "https://gra.gov.gh/qr/...", 
  "submitted_at": "2026-02-10T10:00:00Z",
  "completed_at": "2026-02-10T10:05:00Z",
  "error_message": null 
}
```

**Possible `status` values:**
*   `RECEIVED`: The invoice has been received by the platform.
*   `PROCESSING`: The invoice is being transformed and prepared for GRA submission.
*   `PENDING_GRA`: The invoice has been sent to GRA and awaiting their response.
*   `SUCCESS`: The invoice has been successfully verified by GRA.
*   `FAILED`: The invoice submission failed (details in `error_message`).

### 4.3. Webhook Configuration (Optional)

This endpoint allows businesses to register a webhook URL to receive asynchronous notifications about invoice submission status changes.

*   **Endpoint:** `POST /api/v1/external/webhooks`
*   **Description:** Registers or updates a webhook URL for status notifications.
*   **Authentication:** API Key and Signature.
*   **Request Body (JSON Example):**

```json
{
  "webhook_url": "https://yourbusiness.com/gra-invoice-updates",
  "events": ["invoice.success", "invoice.failed"]
}
```

*   **Response (200 OK - JSON Example):**

```json
{
  "message": "Webhook registered successfully."
}
```

## 5. Error Handling

The API will return standard HTTP status codes and a consistent JSON error response format.

| HTTP Status Code | Error Code | Description                                  |
| :--------------- | :--------- | :------------------------------------------- |
| `400 Bad Request`  | `INVALID_INPUT`  | The request payload is malformed or invalid. |
| `401 Unauthorized` | `AUTH_FAILED`    | Invalid API Key or signature.                |
| `403 Forbidden`    | `ACCESS_DENIED`  | Insufficient permissions.                    |
| `404 Not Found`    | `NOT_FOUND`      | The requested resource does not exist.       |
| `429 Too Many Requests` | `RATE_LIMIT_EXCEEDED` | Rate limit for the business has been exceeded. |
| `500 Internal Server Error` | `SERVER_ERROR`   | An unexpected error occurred on the server.  |
| `503 Service Unavailable` | `GRA_UNAVAILABLE` | GRA API is currently unavailable.            |

**Error Response Example:**

```json
{
  "error_code": "INVALID_INPUT",
  "message": "Validation failed: invoice_number is required."
}
```

## 6. Security Considerations

*   **API Key/Secret Management:** API Keys and Secrets must be stored securely by businesses and never exposed publicly.
*   **HTTPS Only:** All API communication will be enforced over HTTPS.
*   **Rate Limiting:** Implement rate limiting to prevent abuse and protect against DoS attacks.
*   **Input Validation:** Strict validation of all incoming request data to prevent injection attacks and ensure data integrity.
*   **Logging and Monitoring:** Comprehensive logging of API requests and responses for auditing and troubleshooting, with sensitive data masked.
*   **Tenant Isolation:** Ensure that each business can only access and manage its own data.

## 7. Data Transformation Logic (Summary)

Upon receiving an invoice submission, the API will perform the following key transformations:

1.  **Authentication & Authorization:** Verify the API Key and signature against registered businesses.
2.  **Data Validation:** Validate the incoming payload against the defined schema for the external API.
3.  **Field Mapping:** Map the external API fields to the internal `transactions` table schema and subsequently to the GRA E-VAT API fields.
4.  **Levy Calculation & Disaggregation:** Automatically calculate and disaggregate `levyAmountA` (NHIL), `levyAmountB` (GETFund), and set `levyAmountC`, `levyAmountD`, `levyAmountE` to `0.00` based on the 2026 tax reforms, using the `base_amount` provided by the business.
5.  **Queueing:** Place the transformed transaction into the existing internal transaction queue for asynchronous processing and submission to the GRA E-VAT API.
6.  **Status Updates:** Update the submission status internally and trigger webhooks if configured by the business. 

This design leverages the existing FastAPI backend and PostgreSQL database, extending its capabilities to external business integrations while maintaining security and data integrity. 
