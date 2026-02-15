# Integration Best Practices and Error Handling Guide

## 1. Introduction

This document provides essential guidelines for integrating with the External Integration API for GRA invoice submission. It covers best practices for a smooth integration process, a comprehensive error handling strategy, and details on using webhooks for asynchronous notifications.

## 2. Integration Best Practices

Adhering to these best practices will ensure a robust and reliable integration.

### 2.1. Secure Credential Management

*   **Never hardcode API keys or secrets** in your application code. Use environment variables or a secure secrets management system to store and access your credentials.
*   **Rotate your API secrets periodically** to minimize the risk of a compromised secret.

### 2.2. Idempotent Requests

To prevent duplicate submissions, especially in case of network errors or timeouts, your system should handle retries gracefully. While the External Integration API will have its own idempotency mechanisms, it is good practice to include a unique identifier from your system (e.g., `erp_reference_id`) in your requests. This allows for easier reconciliation and troubleshooting.

### 2.3. Efficient Polling Strategy

If you are not using webhooks, implement an efficient polling strategy to check the status of your submissions. Use an **exponential backoff** approach to avoid overwhelming the API with frequent requests, especially for long-running submissions.

### 2.4. Logging and Monitoring

Maintain detailed logs of all API requests and responses on your end. This will be invaluable for debugging integration issues. Monitor the success and failure rates of your submissions to proactively identify and address any problems.

## 3. Error Handling

The External Integration API will use standard HTTP status codes to indicate the success or failure of a request. Your integration should be designed to handle these responses appropriately.

### 3.1. Standard HTTP Error Codes

| HTTP Status Code        | Error Code              | Description                                                                                                | Recommended Action                                                                                             |
| :---------------------- | :---------------------- | :--------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------- |
| `400 Bad Request`       | `INVALID_INPUT`         | The request payload is malformed, contains invalid data, or fails validation checks.                       | **Do not retry.** Check the error message for details, correct the data in your system, and submit a new request. |
| `401 Unauthorized`      | `AUTH_FAILED`           | The provided API Key is invalid, the signature is incorrect, or the account is inactive.                   | **Do not retry.** Verify your API credentials and the signature generation logic.                                |
| `404 Not Found`         | `NOT_FOUND`             | The requested resource (e.g., a submission ID) does not exist.                                             | **Do not retry.** Ensure you are using the correct identifier for the resource.                                  |
| `429 Too Many Requests` | `RATE_LIMIT_EXCEEDED`   | You have exceeded the number of allowed requests in a given time frame.                                    | **Retry with backoff.** Implement an exponential backoff strategy before retrying the request.                 |
| `500 Internal Server Error` | `SERVER_ERROR`          | An unexpected error occurred on the server.                                                                | **Retry with backoff.** This is a transient server-side issue. Wait and retry the request.                     |
| `503 Service Unavailable` | `GRA_UNAVAILABLE`       | The GRA E-VAT API is currently unavailable or not responding.                                              | **Retry with backoff.** This indicates a temporary issue with the upstream GRA system. Wait and retry.           |

### 3.2. Error Response Format

In case of an error, the API will return a JSON response with a consistent format:

```json
{
  "error_code": "INVALID_INPUT",
  "message": "Validation failed: invoice_number is required."
}
```

Your system should parse this response to understand the cause of the error and take appropriate action.

## 4. Webhooks for Asynchronous Notifications

For a more efficient and real-time integration, we highly recommend using **webhooks**. Instead of polling for status updates, you can register a webhook URL, and the External Integration API will send a `POST` request to your URL whenever the status of a submission changes.

### 4.1. How Webhooks Work

1.  **Register your webhook URL** using the `POST /api/v1/external/webhooks` endpoint.
2.  When a submission's status changes (e.g., from `PENDING_GRA` to `SUCCESS`), the API will send a JSON payload to your registered URL.
3.  Your system should acknowledge receipt of the webhook by returning a `200 OK` status code.

### 4.2. Webhook Payload Example

```json
{
  "event_type": "invoice.success",
  "timestamp": "2026-02-10T10:05:00Z",
  "data": {
    "submission_id": "uuid_of_submission",
    "invoice_number": "BIZ-INV-2026-001",
    "status": "SUCCESS",
    "gra_invoice_id": "GRA-INV-2026-001",
    "gra_qr_code": "https://gra.gov.gh/qr/...",
    "completed_at": "2026-02-10T10:05:00Z"
  }
}
```

### 4.3. Securing Your Webhooks

To ensure that the webhook requests are genuinely from the External Integration API, you should **verify the signature** of each incoming webhook. The API will include a signature in the request headers (e.g., `X-Webhook-Signature`), which you can validate using your API Secret.

## 5. Conclusion

By following these integration best practices and implementing a robust error handling strategy, you can build a reliable and resilient integration with the GRA invoice submission system. Utilizing webhooks will further enhance the efficiency and real-time responsiveness of your application.
