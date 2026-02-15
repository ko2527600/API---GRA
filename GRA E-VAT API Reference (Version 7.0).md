# GRA E-VAT API Reference (Version 7.0)

This document provides a comprehensive list of all API endpoints available in the GRA E-VAT system for integration.

## 1. Base URLs
*   **Sandbox/Test:** `https://apitest.e-vatgh.com/evat_apiqa/`
*   **Production:** (Provided upon certification)

---

## 2. API Endpoints Summary

| Category | Action | Method | Endpoint | Format |
| :--- | :--- | :--- | :--- | :--- |
| **Invoice** | Send Invoice | POST | `post_receipt_Json.jsp` | JSON |
| **Invoice** | Send Invoice | POST | `post_receipt.jsp` | XML |
| **Refund** | Send Refund | POST | `post_receipt_Json.jsp` | JSON |
| **Refund** | Send Refund | POST | `post_receipt.jsp` | XML |
| **Signature** | Request Signature | POST | `get_Response_JSON.jsp` | JSON |
| **Signature** | Request Signature | POST | `get_Response_JSON.jsp` | XML |
| **Items** | Item Code Request | POST | `post_Item_JSON.jsp` | JSON |
| **Items** | Item Code Request | POST | `post_Item.jsp` | XML |
| **Purchase** | Send Purchase | POST | `post_receipt_Json.jsp` | JSON |
| **Purchase** | Send Purchase | POST | `post_receipt.jsp` | XML |
| **Purchase** | Cancel Purchase | POST | `post_receipt_Json.jsp` | JSON |
| **Inventory** | Send Inventory | POST | `post_Inventory_JSON.jsp` | JSON |
| **Inventory** | Send Inventory | POST | `post_Inventory.jsp` | XML |
| **TIN Validator** | Validate TIN | POST | `tin_validator_JSON.jsp` | JSON |
| **TIN Validator** | Validate TIN | POST | `tin_validator.jsp` | XML |
| **Health Check** | VSDC Health Check | POST | `health_check_request_JSON.jsp` | JSON |
| **Health Check** | VSDC Health Check | POST | `health_check_request.jsp` | XML |
| **Z Report** | Request Z Report | POST | `requestZd_report_Json.jsp` | JSON |
| **Z Report** | Request Z Report | POST | `zReport.jsp` | XML |

---

## 3. Detailed Endpoint Descriptions

### **3.1. Invoices & Refunds**
Used to submit sales transactions or process refunds.
*   **JSON Endpoint:** `https://apitest.e-vatgh.com/evat_apiqa/post_receipt_Json.jsp`
*   **Key Fields:** `FLAG` (set to `"INVOICE"` or `"REFUND"`), `TOTAL_VAT`, `TOTAL_AMOUNT`, `item_list`.

### **3.2. Signature Requests**
Used to retrieve the digital signature and VSDC data for a previously submitted invoice.
*   **JSON Endpoint:** `https://apitest.e-vatgh.com/evat_apiqa/get_Response_JSON.jsp`
*   **Key Fields:** `NUM` (Invoice Number), `FLAG` (Type of transaction).

### **3.3. Item Management**
Used to register or update item codes in the GRA system.
*   **JSON Endpoint:** `https://apitest.e-vatgh.com/evat_apiqa/post_Item_JSON.jsp`
*   **Key Fields:** `ITEM_NAME`, `ITEM_CATEGORY`, `TAXCODE`.

### **3.4. Inventory Management**
Used to sync inventory levels with the GRA.
*   **JSON Endpoint:** `https://apitest.e-vatgh.com/evat_apiqa/post_Inventory_JSON.jsp`
*   **Key Fields:** `NIKI_CODE`, `QUANTITY`.

### **3.5. TIN Validation**
Used to verify if a client's TIN is valid before issuing an invoice.
*   **JSON Endpoint:** `https://apitest.e-vatgh.com/evat_apiqa/tin_validator_JSON.jsp`
*   **Key Fields:** `TIN`.

### **3.6. VSDC Health Check**
Used to verify if the Virtual Sales Data Controller (VSDC) is online and responsive.
*   **JSON Endpoint:** `https://apitest.e-vatgh.com/evat_apiqa/health_check_request_JSON.jsp`
*   **Key Fields:** `CMD` (usually `"ID REQUEST"`).

### **3.7. Z Reports**
Used to generate the daily summary report required for tax compliance.
*   **JSON Endpoint:** `https://apitest.e-vatgh.com/evat_apiqa/requestZd_report_Json.jsp`
*   **Key Fields:** `COMPANY_TIN`.

---

## 4. Authentication Requirements
All requests must include the following in the `company` object of the JSON body:
*   `COMPANY_TIN`
*   `COMPANY_NAMES`
*   `COMPANY_SECURITY_KEY`

Additionally, some versions may require the `COMPANY_SECURITY_KEY` to be sent as an HTTP Header.
