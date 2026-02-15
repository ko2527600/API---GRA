# GRA E-VAT Sandbox (Test Environment) Details

To test your API safely, use the following Sandbox details provided in the official GRA documentation.

## 1. Sandbox Base URL
All test requests should be sent to the following base URL:
`https://apitest.e-vatgh.com/evat_apiqa/`

### **Common Test Endpoints:**
*   **Submit Invoice (JSON):** `https://apitest.e-vatgh.com/evat_apiqa/post_receipt_Json.jsp`
*   **Submit Invoice (XML):** `https://apitest.e-vatgh.com/evat_apiqa/post_receipt.jsp`
*   **TIN Validator (JSON):** `https://apitest.e-vatgh.com/evat_apiqa/tin_validator_JSON.jsp`

---

## 2. Test Credentials (Authentication)
Use these credentials in the `company` object of your JSON request body to authenticate with the Sandbox:

| Field | Value |
| :--- | :--- |
| **COMPANY_TIN** | `C00XXXXXXXX` |
| **COMPANY_NAMES** | `TEST TAXPAYER 15 PERCENT VAT` |
| **COMPANY_SECURITY_KEY** | `UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH` |

---

## 3. How to Use the Sandbox
1.  **Set the URL**: Point your middleware to the Sandbox URL instead of the production one.
2.  **Use Test Data**: Use the credentials above.
3.  **Verify Response**: A successful test will return a `200 OK` status and a `signature` field in the response.

> **Note:** The Sandbox environment is for testing logic and formatting only. Data sent here does not affect real tax records.
