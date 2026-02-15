# GRA External Integration API: Comprehensive Guidelines and Technical Design

## 1. Executive Summary

This document provides a comprehensive set of guidelines and a technical design for an **External Integration API** that allows registered businesses in Ghana to seamlessly integrate their Enterprise Resource Planning (ERP) or accounting systems with the **GRA ERP Integration Platform**. This API serves as a secure and efficient gateway for submitting invoices to the **Ghana Revenue Authority (GRA) E-VAT system** for real-time verification and compliance.

By abstracting the complexities of the GRA's internal E-VAT API and automating critical data transformations—such as the disaggregation of levies according to the 2026 tax reforms—this API simplifies the compliance burden for businesses while ensuring data accuracy and security.

---

## 2. API Architecture and Security

The External Integration API is designed as a robust, scalable, and secure interface based on RESTful principles.

### 2.1. Architectural Principles

*   **RESTful Design**: Utilizes standard HTTP methods and resource-based endpoints for clarity and ease of integration.
*   **Statelessness**: Each request contains all necessary information, enhancing reliability and scalability.
*   **Versioning**: Employs clear versioning (e.g., `/v1/`) to ensure backward compatibility as the platform evolves.

### 2.2. Security Framework

*   **Authentication**: Businesses authenticate using a unique **API Key** and an **HMAC Signature** generated with a secure **API Secret**. This ensures that every request is authenticated and has not been tampered with.
*   **Encryption**: All data in transit is protected by **HTTPS (TLS 1.2+)**. Sensitive credentials are encrypted at rest using a dedicated secrets management system.
*   **Tenant Isolation**: Strict multi-tenant isolation ensures that businesses can only access and manage their own data.
*   **Rate Limiting**: Protects the API from abuse and ensures consistent performance for all users.

---

## 3. Data Transformation and Mapping Standards

A core function of the API is to transform business-provided invoice data into the specific format required by the GRA E-VAT API.

### 3.1. 2026 Ghana Tax Reform Compliance

The API automatically handles the disaggregation of levies based on the latest 2026 reforms:

| Component | Rate | GRA API Field | Description |
| :--- | :--- | :--- | :--- |
| **VAT** | 15% | `totalVat` | Standard Value Added Tax. |
| **NHIL** | 2.5% | `levyAmountA` | National Health Insurance Levy. |
| **GETFund** | 2.5% | `levyAmountB` | Ghana Education Trust Fund Levy. |
| **COVID Levy** | 0% | `levyAmountC` | Abolished as of 2026. |

### 3.2. Mapping Logic Example

For a transaction with a base amount of **GHS 100.00**, the API will perform the following calculations:

| Field | Calculation | Amount (GHS) |
| :--- | :--- | :--- |
| `unitPrice` | Base Amount | 100.00 |
| `levyAmountA` | 100 × 0.025 | 2.50 |
| `levyAmountB` | 100 × 0.025 | 2.50 |
| `totalLevy` | 2.50 + 2.50 | **5.00** |
| `totalVat` | 100 × 0.15 | 15.00 |
| `totalAmount` | 100 + 5 + 15 | **120.00** |

---

## 4. API Endpoints Reference

### 4.1. Submit Invoice
*   **Endpoint**: `POST /api/v1/external/invoices`
*   **Purpose**: Submits a new invoice for GRA verification.
*   **Key Payload Fields**: `invoice_number`, `customer_name`, `transaction_date`, `items`, `base_amount`, `total_vat`, `total_levy`, `total_amount`.

### 4.2. Get Submission Status
*   **Endpoint**: `GET /api/v1/external/invoices/{submission_id}/status`
*   **Purpose**: Retrieves the real-time status of a submission, including the GRA-issued Invoice ID and QR code URL upon success.

---

## 5. Integration Best Practices and Error Handling

### 5.1. Best Practices
*   **Secure Credentials**: Use environment variables or secrets managers; never hardcode keys.
*   **Webhooks**: Implement webhooks for real-time, asynchronous status updates instead of frequent polling.
*   **Idempotency**: Use your internal reference IDs to prevent duplicate submissions during retries.

### 5.2. Error Handling Strategy
The API uses standard HTTP status codes. Integrations should implement **exponential backoff** for transient errors (5xx) and rate limits (429), while treating validation errors (400) as final until the data is corrected.

---

## 6. Conclusion

These guidelines provide the technical foundation for building a high-quality integration with the GRA ERP Integration Platform. By following these standards, businesses can ensure their invoice submission process is secure, compliant, and highly efficient.

---

## References

[1] Ghana Revenue Authority. (2024). "E-VAT Integration Guide."  
[2] Ghana Revenue Authority. (2024). "E-VAT API Documentation Version 8.1."  
[3] Ghana Ministry of Finance. (2026). "Tax Reforms 2026: VAT and Levy Updates."  
[4] GRA ERP Integration Software Documentation. (2026). Internal System Specifications.
