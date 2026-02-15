# GRA E-VAT API Technical Specification for System Audit

## 1. Introduction
This document serves as a comprehensive technical specification for the Ghana Revenue Authority (GRA) Electronic Value Added Tax (E-VAT) API. Its primary purpose is to provide a detailed reference for businesses and system integrators, enabling them to audit their existing E-VAT systems against the official GRA requirements. The information contained herein is derived from the official GRA E-VAT API documentation, version 7.0, and aims to cover all critical aspects necessary for a compliant and robust integration [1].

The GRA E-VAT system is a crucial initiative by the Ghanaian government to enhance tax compliance and transparency. It mandates that all VAT-registered businesses issue electronic invoices that are validated and stamped by the GRA's Certified Invoicing System (VCIS) and Virtual Sales Data Controller (VSDC). A successful integration ensures that transaction data is accurately captured and transmitted to the GRA in real-time or near real-time, reducing discrepancies and facilitating efficient tax administration.

## 2. System Architecture and Dataflow
The E-VAT integration involves a client-server architecture where the business's Point of Sale (POS) or Enterprise Resource Planning (ERP) system acts as the **Certified Invoicing System (VCIS)**. This VCIS communicates directly with the GRA's **Virtual Sales Data Controller (VSDC)** via the provided API. The VSDC is responsible for receiving transaction data, applying digital signatures, and stamping the invoices before relaying the information to the central GRA backend. The overall dataflow can be summarized as follows:

1.  **Transaction Generation**: A sales transaction occurs within the business's VCIS (e.g., POS, ERP).
2.  **API Request**: The VCIS formats the transaction data (invoice, refund, item update, etc.) into either JSON or XML format, including the mandatory company authentication details.
3.  **API Submission**: The formatted data is sent via HTTP POST request to the appropriate GRA E-VAT API endpoint.
4.  **VSDC Processing**: The VSDC receives the request, validates the data and authentication credentials, processes the transaction, and generates a unique digital stamp (signature).
5.  **API Response**: The VSDC sends back a response to the VCIS, which includes the status of the transaction, any generated identifiers (like `ysdcid`, `ysdcrecnum`), and potentially error codes if validation fails.
6.  **Invoice Printing**: Upon successful receipt of the VSDC response, the VCIS can then print the official E-VAT invoice, incorporating the digital stamp details.
7.  **GRA Backend Integration**: The VSDC automatically forwards the processed transaction data to the central GRA E-VAT backend for record-keeping and auditing purposes.

This architecture ensures that all invoices are centrally recorded and verified by the tax authority, providing a robust mechanism for VAT collection and compliance.

## 3. Authentication
All interactions with the GRA E-VAT API require robust authentication to ensure that only authorized businesses submit data. Authentication is not handled via traditional API keys in headers but rather by embedding specific company credentials directly within the request body of every API call. This approach links each transaction directly to the originating taxpayer. The following three parameters are **mandatory** for the `company` object in every request:

*   **`COMPANY_TIN`**: This represents the **Taxpayer Identification Number** of the company. It is a unique identifier assigned by the GRA. The documentation specifies that this field must be either **11 or 15 characters** long. Example: `C00XXXXXXXX`.
*   **`COMPANY_NAMES`**: This is the **legal registered name** of the company as it appears in GRA records. It must precisely match the name associated with the provided `COMPANY_TIN`. Example: `TEST TAXPAYER 15 PERCENT VAT`.
*   **`COMPANY_SECURITY_KEY`**: This is a **unique alphanumeric security key** provided by the GRA specifically for API integration. It acts as a shared secret to authenticate the company's requests. The key is typically **32 characters** long. Example: `UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH`.

**Example Authentication Block (JSON)**:
```json
"company": {
  "COMPANY_NAMES": "TEST TAXPAYER 15 PERCENT VAT",
  "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
  "COMPANY_TIN": "C00XXXXXXXX"
}
```

Any discrepancy in these authentication parameters will result in an `A01` error code, indicating that the company details do not exist or are incorrect, and the transaction will be rejected.

## 4. Supported Data Formats
The GRA E-VAT API offers flexibility by supporting two widely used data interchange formats for submitting transaction data:

### 4.1. JSON Format
**JSON (JavaScript Object Notation)** is a lightweight, human-readable, and easy-to-parse data format. It is widely adopted in modern web services due to its simplicity and efficiency. When using JSON, the request body should be structured as a JSON object, with appropriate data types for each field (strings, numbers, arrays, etc.). This format is generally recommended for its ease of implementation and debugging.

**Content-Type Header for JSON**: `application/json`

### 4.2. XML Format
**XML (Extensible Markup Language)** is a markup language that defines a set of rules for encoding documents in a format that is both human-readable and machine-readable. It is often preferred in enterprise systems for its strict schema validation capabilities, which can enforce data integrity. When using XML, the request body should be a well-formed XML document adhering to the API's specified structure.

**Content-Type Header for XML**: `application/xml`

Both formats serve the same purpose of transmitting transaction data to the GRA E-VAT system. The choice between JSON and XML typically depends on the existing infrastructure and preferences of the integrating system. However, consistency in using one format for all transactions from a single VCIS is advisable.

## 5. API Modules and Endpoints
The GRA E-VAT API is structured into several modules, each addressing a specific business process related to electronic invoicing. Below are the key modules, their functionalities, and the corresponding API endpoints (using the test environment URLs for demonstration) [1]:

### 5.1. Invoice / Refund Module
This module is central to the E-VAT system, handling the submission of sales invoices and refund transactions. It supports both JSON and XML formats.

*   **JSON Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/post_receipt_Json.jsp`
*   **XML Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/post_receipt.jsp`

#### Request Structure for Invoice/Refund (JSON Example)
The request body for an invoice or refund submission is complex and contains several nested objects:

```json
{
  "company": { /* Authentication block as described in Section 3 */ },
  "header": {
    "COMPUTATION_TYPE": "INCLUSIVE", // or "EXCLUSIVE". Defines how VAT/Levies are applied.
    "FLAG": "INVOICE",             // or "REFUND", "PROFORMA", "PARTIAL_REFUND", "PURCHASE"
    "SALE_TYPE": "NORMAL",          // e.g., "NORMAL", "CREDIT_SALE"
    "USER_NAME": "ARNAU",           // Name of the user performing the transaction
    "NUM": "SAP12320t01",           // Unique invoice/receipt number from VCIS
    "REFUND_ID": "DEMREF001",       // Mandatory for refunds, links to original invoice
    "INVOICE_DATE": "2020-07-15",   // Date of the invoice/refund (YYYY-MM-DD)
    "CURRENCY": "GHS",              // Currency of the transaction. Default is GHS.
    "EXCHANGE_RATE": "1",           // Exchange rate if currency is not GHS. Must be "1" for GHS.
    "CLIENT_TIN": "C0022825405",     // Customer's TIN (if available)
    "CLIENT_TIN_PIN": "2222",       // Customer's TIN PIN (if available)
    "CLIENT_NAME": "Elissa",        // Customer's name
    "TOTAL_VAT": "159",             // Total VAT amount for the transaction
    "TOTAL_LEVY": "60",             // Total Levy amount for the transaction
    "TOTAL_AMOUNT": "3438",         // Grand total amount of the invoice/refund
    "ITEMS_COUNTS": "2",            // Number of distinct items in the item_list
    "VOUCHER_AMOUNT": "0",          // Amount of any voucher used
    "DISCOUNT_TYPE": "GENERAL",     // Type of discount applied (e.g., "GENERAL", "ITEM_SPECIFIC")
    "DISCOUNT_AMOUNT": "0",         // Total discount amount
    "FILE_NAME": "",                // Optional: Name of an associated file
    "CALL_BACK": "http://host/receiptCallback.php" // Optional: Callback URL for asynchronous responses
  },
  "item_list": [
    {
      "ITMREF": "MANGO01",          // Item reference code
      "ITMDES": "Mango juice",        // Item description
      "TAXRATE": "0",               // Tax rate applicable to this item (e.g., "0", "15", "3")
      "TAXCODE": "A",               // Tax code applicable to this item (e.g., "A", "B", "C", "D", "E")
      "LEVY_AMOUNT_A": "0",         // Amount of Levy A for this item
      "LEVY_AMOUNT_B": "0",         // Amount of Levy B for this item
      "LEVY_AMOUNT_C": "0",         // Amount of Levy C for this item
      "LEVY_AMOUNT_D": "0",         // Amount of Levy D for this item
      "QUANTITY": "20",             // Quantity of the item
      "UNITYPRICE": "100",          // Unit price of the item
      "ITMDISCOUNT": "0",           // Discount applied to this specific item
      "BATCH": "",                  // Optional: Batch number
      "EXPIRE": "",                 // Optional: Expiry date
      "ITEM_CATEGORY": "JUICE"      // Category of the item
    },
    { /* ... additional items ... */ }
  ]
}
```

#### Important Considerations for Invoice/Refund:
*   **`FLAG` Field**: This field determines the type of transaction. Ensure it is correctly set (e.g., `INVOICE` for sales, `REFUND` for returns).
*   **`REFUND_ID`**: For refund transactions, this field is crucial and must reference the `NUM` of the original invoice being refunded. An `A05` error will occur if missing.
*   **`COMPUTATION_TYPE`**: This dictates whether the `UNITYPRICE` includes or excludes VAT and levies. This is critical for accurate tax calculations.
*   **Total Fields**: `TOTAL_VAT`, `TOTAL_LEVY`, and `TOTAL_AMOUNT` in the header must accurately reflect the sum of all items and their respective taxes/levies. Discrepancies will trigger validation errors like `B16` or `B18`.
*   **`ITEMS_COUNTS`**: Must be an accurate count of items in the `item_list` array.

### 5.2. Signature Request (Stamping)
After a successful invoice or refund submission, the VCIS needs to retrieve the digital signature details from the VSDC to be printed on the physical invoice. This is often referred to as 
the "stamping" process. The API endpoint for this request is:

*   **JSON Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/get_Response_JSON.jsp`

#### Purpose of Signature Request:
This endpoint is used to retrieve the unique identifiers and data generated by the VSDC after a successful transaction (invoice, refund, etc.). These details are essential for printing on the physical invoice or receipt, serving as proof of GRA validation. Key information returned includes:

*   **`ysdcid`**: The unique identifier of the VSDC that processed the transaction.
*   **`ysdcrecnum`**: The VSDC receipt number.
*   **`ysdcintdata`**: Integrated data from the VSDC.
*   **`ysdcnrc`**: VSDC serial number.

### 5.3. Items & Inventory Module
This module facilitates the management of item codes and inventory updates within the E-VAT system. It is crucial for ensuring that product information and stock levels are accurately reflected in the GRA system.

#### 5.3.1. Item Code Request
This endpoint is used to register or update item codes and their associated details with the GRA E-VAT system. This ensures that all products or services sold by a business are recognized and categorized correctly for tax purposes.

*   **JSON Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/post_item_JSON.jsp`
*   **XML Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/post_item.jsp`

#### Request Structure for Item Code Request (JSON Example)
```json
{
  "company": { /* Authentication block */ },
  "item_list": [
    {
      "ITEM_NAME": "HEINEKEN",      // Name of the item
      "ITEM_CATEGORY": "BEER",    // Category of the item
      "ITEM_REF": "HEIN001",      // Unique reference code for the item
      "TAX_CODE": "B",            // Tax code applicable to the item
      "QTY": "250"                // Quantity (if applicable, e.g., for initial stock or batch)
    }
  ]
}
```

#### Important Considerations for Item Code Request:
*   **`ITEM_REF`**: This should be a unique identifier for each product or service. Consistency is key.
*   **`TAX_CODE`**: Ensure the correct tax code is assigned to each item based on its taxability (refer to Section 6.2).

#### 5.3.2. Inventory Update
This endpoint allows businesses to update their inventory levels with the GRA E-VAT system. This can be used for initial stock registration or periodic updates.

*   **JSON Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/post_inventory_JSON.jsp`
*   **XML Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/post_inventory.jsp`

#### Request Structure for Inventory Update (JSON Example)
```json
{
  "company": { /* Authentication block */ },
  "item_list": [
    {
      "NIKI_CODE": "BEEHEIN00011", // Unique inventory code
      "ITEM_CODE": "1000P1322",    // Item reference code
      "QTY": "250"                 // Current quantity in stock
    }
  ]
}
```

#### Important Considerations for Inventory Update:
*   **`NIKI_CODE`**: This appears to be a unique identifier for an inventory record. Further clarification might be needed from GRA if its generation is not straightforward.
*   **`ITEM_CODE`**: This should correspond to the `ITEM_REF` used in the Item Code Request.

### 5.4. TIN Validator Module
The TIN Validator module provides a mechanism to verify the validity and status of a customer's Taxpayer Identification Number (TIN) before issuing an invoice. This helps in ensuring that transactions are recorded against legitimate taxpayers.

*   **JSON Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/tin_validator_JSON.jsp`
*   **XML Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/tin_validator.jsp`

#### Request Structure for TIN Validator (JSON Example)
```json
{
  "company": { /* Authentication block */ },
  "CLIENT_TIN_PIN": "123456789", // Client's TIN PIN
  "TIN": "C1076104711"          // Client's TIN
}
```

#### Important Considerations for TIN Validator:
*   **`TIN`**: The client's TIN must be provided. It should adhere to the 11 or 15 character length requirement.
*   **`CLIENT_TIN_PIN`**: This is likely a personal identification number associated with the client's TIN.
*   **Response**: A successful response will typically confirm the validity of the TIN and may return the taxpayer's name. Error codes like `T01`, `T03`, `T04`, `T05`, `T06` indicate issues with the TIN.

### 5.5. VSDC Health Check Module
This module allows the VCIS to check the operational status of the VSDC. It's a crucial utility for monitoring the health and availability of the E-VAT integration components.

*   **JSON Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/health_check_request_JSON.jsp`
*   **XML Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/health_check_request.jsp`

#### Request Structure for VSDC Health Check (JSON Example)
```json
{
  "company": { /* Authentication block */ },
  "CMD": "ID REQUEST", // Command to request VSDC ID
  "TIME": "2022-09-25"   // Current timestamp
}
```

#### Important Considerations for VSDC Health Check:
*   **`CMD`**: The command `ID REQUEST` is used to query the VSDC for its identifier.
*   **Response**: A successful response will indicate that the VSDC is up and running, and will return the `SDC_ID`.

### 5.6. Z-Report Module
The Z-Report module is used to retrieve summarized sales data for a specific period, typically for end-of-day reporting. This report provides aggregated figures for auditing and reconciliation purposes.

*   **JSON Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/requestZd_report_Json.jsp`
*   **XML Endpoint**: `POST https://apitest.e-vatgh.com/evat_apiqa/zReport.jsp`

#### Request Structure for Z-Report (JSON Example)
```json
{
  "company": { /* Authentication block */ },
  "ZD_DATE": "2022-12-1" // Date for which the Z-Report is requested (YYYY-MM-DD)
}
```

#### Important Considerations for Z-Report:
*   **`ZD_DATE`**: The date for which the Z-Report is being requested. Ensure the format is `YYYY-MM-DD`.
*   **Response**: The Z-Report response will include aggregated data such as `inv_close` (closed invoices), `inv_count` (total invoice count), `inv_open` (open invoices), `inv_vat` (total VAT), `inv_total` (grand total), and `inv_levy` (total levies).

## 6. Tax and Levy Calculations
Accurate calculation of taxes and levies is paramount for compliance. The GRA E-VAT API documentation specifies distinct categories for levies and tax codes, each with its own rate and application rules. Businesses must ensure their systems correctly implement these calculations.

### 6.1. Levies Mapping
Ghanaian tax regulations include several levies that apply to goods and services. These are represented in the API as follows:

| Levy Code | Description                                  | Rate   | Calculation Basis                                   |
| :-------- | :------------------------------------------- | :----- | :-------------------------------------------------- |
| `LEVY_A`  | **National Health Insurance Levy (NHIL)**    | 2.5%   | Applied to the taxable value of goods/services.     |
| `LEVY_B`  | **Ghana Education Trust Fund Levy (GETFL)**  | 2.5%   | Applied to the taxable value of goods/services.     |
| `LEVY_C`  | **COVID-19 Health Recovery Levy**            | 1%     | Applied to the taxable value of goods/services.     |
| `LEVY_D`  | **Tourism Levy / Communication Service Tax (CST)** | 1% / 5% | Tourism Levy on specific services; CST on communication services. |

**Note**: The specific application of `LEVY_D` (Tourism/CST) can vary based on the nature of the service or product. Businesses should consult the latest GRA guidelines for precise application rules.

### 6.2. Tax Code Mapping to Tax Rate
The API uses specific tax codes to categorize items based on their taxability and apply the corresponding VAT rate:

| Tax Code | Description   | Rate  | Application                                       |
| :------- | :------------ | :---- | :------------------------------------------------ |
| `TAX_A`  | **Exempted**  | 0%    | For goods/services explicitly exempted from VAT.  |
| `TAX_B`  | **Taxable**   | 15%   | Standard VAT rate for most goods and services.    |
| `TAX_C`  | **Export**    | 0%    | For goods/services exported out of Ghana.         |
| `TAX_D`  | **Non Taxable** | 0%    | For goods/services that are not subject to VAT.   |
| `TAX_E`  | **Non VAT**   | 3%    | A flat rate applied to specific non-VAT supplies. |

### 6.3. Calculation Logic (Critical Audit Point)
The order and basis of calculation are crucial. Based on typical VAT systems and the provided documentation, the following general calculation logic should be applied:

1.  **Item Price**: Start with the base unit price of the item.
2.  **Levies Calculation**: Apply `LEVY_A`, `LEVY_B`, and `LEVY_C` to the item's price. The sum of these levies is added to the item's price to form a 'levy-inclusive' base for VAT calculation.
    *   `Item_Price_Plus_Levies = UNITYPRICE + (UNITYPRICE * LEVY_A_Rate) + (UNITYPRICE * LEVY_B_Rate) + (UNITYPRICE * LEVY_C_Rate)`
3.  **VAT Calculation (for `TAX_B` - 15%)**: VAT is typically calculated on the `Item_Price_Plus_Levies`.
    *   `VAT_Amount = Item_Price_Plus_Levies * TAX_B_Rate`
4.  **`LEVY_D` Calculation**: If applicable, `LEVY_D` (Tourism/CST) is calculated separately, often on the base price or a specific service component.
5.  **Total Item Amount**: Sum of `UNITYPRICE` + all applicable `LEVY_AMOUNTS` + `VAT_Amount`.

**Example Scenario (for `TAX_B` item with all levies):**
*   `UNITYPRICE` = 100 GHS
*   `LEVY_A` (NHIL) = 2.5%
*   `LEVY_B` (GETFL) = 2.5%
*   `LEVY_C` (COVID) = 1%
*   `TAX_B` (VAT) = 15%

1.  `LEVY_A_Amount = 100 * 0.025 = 2.5 GHS`
2.  `LEVY_B_Amount = 100 * 0.025 = 2.5 GHS`
3.  `LEVY_C_Amount = 100 * 0.01 = 1 GHS`
4.  `Base_for_VAT = 100 + 2.5 + 2.5 + 1 = 106 GHS`
5.  `VAT_Amount = 106 * 0.15 = 15.9 GHS`
6.  `Total_Item_Amount = 100 + 2.5 + 2.5 + 1 + 15.9 = 121.9 GHS`

**Note**: For `COMPUTATION_TYPE: 
INCLUSIVE` (VAT and levies are included in the `UNITYPRICE`), the calculation logic would be reversed to extract the net price before applying taxes and levies. This requires careful implementation to avoid rounding errors.

## 7. Validation Rules and Error Codes
The GRA E-VAT API implements a robust set of validation rules to ensure data integrity and compliance. Understanding these rules and the corresponding error codes is critical for developing a resilient integration. The API returns specific error codes in its response when a validation rule is violated. Below is a detailed breakdown of common error codes and their implications [1]:

### 7.1. Authentication Errors
*   **`A01`**: **COMPANY_NAMES: COMPANY_TIN: COMPANY_SECURITY_KEY: DOES NOT EXISTS**
    *   **Description**: This error indicates that the provided company authentication credentials (TIN, name, or security key) do not match any registered entity in the GRA system. This could be due to a typo, incorrect credentials, or an unregistered company.
    *   **Action**: Verify the `COMPANY_TIN`, `COMPANY_NAMES`, and `COMPANY_SECURITY_KEY` against the credentials provided by GRA. Ensure they are exact matches, including case sensitivity.
*   **`B01`**: **INCORRECT CLIENT TIN PIN**
    *   **Description**: The `CLIENT_TIN_PIN` provided for a customer is incorrect.
    *   **Action**: Verify the client's TIN PIN. This is typically used in the TIN Validator module.

### 7.2. Invoice/Refund Header Validation Errors
*   **`B16`**: **INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT**
    *   **Description**: The `TOTAL_AMOUNT` specified in the invoice header does not match the sum of all item amounts (including VAT and levies) in the `item_list`.
    *   **Action**: Re-calculate the `TOTAL_AMOUNT` by summing up the `UNITYPRICE` of all items, applying all relevant taxes and levies, and ensuring the final sum matches the `TOTAL_AMOUNT` in the header. Pay close attention to `COMPUTATION_TYPE`.
*   **`B18`**: **INVOICE TOTAL TAXES AMOUNT DIFFERENT TAXES**
    *   **Description**: The `TOTAL_VAT` specified in the invoice header does not match the sum of all VAT amounts calculated for individual items in the `item_list`.
    *   **Action**: Verify the calculation of VAT for each item and ensure their sum correctly populates the `TOTAL_VAT` field in the header.
*   **`B19`**: **INVOICE REFERENCE MISSING**
    *   **Description**: The unique invoice reference number (`NUM`) is missing from the header.
    *   **Action**: Ensure a unique invoice number is always provided for each transaction.
*   **`B20`**: **INVOICE REFERENCE ALREADY SENT**
    *   **Description**: An invoice with the same `NUM` (invoice reference) has already been successfully submitted to the GRA E-VAT system.
    *   **Action**: Ensure that each invoice submitted has a unique `NUM`. Implement a mechanism to prevent duplicate submissions.
*   **`B22`**: **ZERO TOTAL INVOICE NOT SUPPORTED**
    *   **Description**: The `TOTAL_AMOUNT` of the invoice is zero or negative, which is not allowed for sales invoices.
    *   **Action**: Ensure that sales invoices always have a positive `TOTAL_AMOUNT`.
*   **`B70`**: **WRONG CURRENCY**
    *   **Description**: The currency specified is not GHS, or the `EXCHANGE_RATE` is not `1` when `CURRENCY` is GHS.
    *   **Action**: For transactions in Ghanaian Cedis, set `CURRENCY` to `GHS` and `EXCHANGE_RATE` to `1`.
*   **`A05`**: **MISSING ORIGINAL INVOICE NUMBER**
    *   **Description**: For refund transactions (`FLAG: 
`REFUND`), the `REFUND_ID` field (which should contain the original invoice number) is missing.
    *   **Action**: Ensure that for all refund transactions, the `REFUND_ID` is correctly populated with the `NUM` of the original invoice being refunded.

### 7.3. Item List Validation Errors
*   **`B05`**: **CLIENT NAME MISSING**
    *   **Description**: The client name (`CLIENT_NAME`) is missing in the invoice header.
    *   **Action**: Ensure `CLIENT_NAME` is always provided.
*   **`B051`**: **TAX NUMBER FORMAT NOT ACCEPTED**
    *   **Description**: The format of the client's tax number (`CLIENT_TIN`) is incorrect (not 11 or 15 characters).
    *   **Action**: Validate the `CLIENT_TIN` to ensure it meets the specified length requirements.
*   **`B06`**: **CLIENT NAME DIFFERENT FOR PREVIOUS ONE**
    *   **Description**: The client name provided for a given `CLIENT_TIN` differs from a previously recorded name for the same TIN.
    *   **Action**: Ensure consistency in client names associated with their TINs. If a name change is legitimate, it might require a specific update process with GRA.
*   **`B061`**: **ITEM CODE DIFFERENT FOR PREVIOUS ONE**
    *   **Description**: The `ITMREF` (item code) for a product differs from a previously recorded item code for the same product.
    *   **Action**: Maintain consistent `ITMREF` for products. If an item code needs to be changed, it might require a specific update process via the Items module.
*   **`B07`**: **CODE MISSING**
    *   **Description**: A required code field (e.g., `ITMREF`, `TAXCODE`) is missing for an item.
    *   **Action**: Ensure all mandatory code fields are populated for each item.
*   **`B09`**: **DESCRIPTION MISSING**
    *   **Description**: The item description (`ITMDES`) is missing.
    *   **Action**: Provide a clear description for each item.
*   **`B10`**: **QUANTITY MISSING**
    *   **Description**: The `QUANTITY` for an item is missing or invalid (e.g., zero for a sale).
    *   **Action**: Ensure `QUANTITY` is a positive number for sales.
*   **`B11`**: **QUANTITY IS NEGATIVE**
    *   **Description**: The `QUANTITY` for an item is negative.
    *   **Action**: Ensure `QUANTITY` is always positive for sales. For returns, use the Refund module.
*   **`B12`**: **QUANTITY NOT A NUMBER**
    *   **Description**: The `QUANTITY` field contains non-numeric characters.
    *   **Action**: Ensure `QUANTITY` is a valid numeric value.
*   **`B13`**: **TAX_RATE NOT ACCEPTED**
    *   **Description**: The `TAXRATE` provided for an item is not one of the accepted values (e.g., `0`, `15`, `3`).
    *   **Action**: Ensure `TAXRATE` corresponds to the valid rates defined by GRA.
*   **`B15`**: **CHECK NUMBER OF ITEMS WITH EXPECTED SIZE**
    *   **Description**: The number of items in `item_list` does not match `ITEMS_COUNTS` in the header.
    *   **Action**: Ensure `ITEMS_COUNTS` accurately reflects the actual number of items in the `item_list` array.
*   **`B21`**: **NEGATIVE SALE PRICE NOT ALLOWED**
    *   **Description**: The `UNITYPRICE` for an item is zero or negative.
    *   **Action**: Ensure `UNITYPRICE` is always positive for sales.
*   **`B27`**: **TAXRATE DIFFERENT FROM PREVIOUS ONE**
    *   **Description**: The `TAXRATE` for a specific item (`ITMREF`) differs from a previously recorded tax rate for the same item.
    *   **Action**: Maintain consistency in `TAXRATE` for items. If a tax rate changes, it might require a specific update process.
*   **`B28`**: **CLIENT TAX NUMBER DIFFERENT FROM PREVIOUS ONE**
    *   **Description**: The `CLIENT_TIN` for a client differs from a previously recorded TIN for the same client.
    *   **Action**: Ensure consistency in client TINs. If a TIN changes, it might require a specific update process with GRA.
*   **`B29`**: **CLIENT TAX NUMBER IS FOR ANOTHER CLIENT**
    *   **Description**: The `CLIENT_TIN` provided is registered to a different client name.
    *   **Action**: Verify the `CLIENT_TIN` and `CLIENT_NAME` match the GRA records.
*   **`B31`**: **LEVY A AMOUNT ARE DIFFERENT**
*   **`B32`**: **LEVY B AMOUNT ARE DIFFERENT**
*   **`B33`**: **LEVY C AMOUNT ARE DIFFERENT**
*   **`B34`**: **TOTAL LEVY AMOUNT ARE DIFFERENT**
*   **`B35`**: **LEVY D AMOUNT ARE DIFFERENT**
    *   **Description (B31-B35)**: These errors indicate discrepancies in the calculated levy amounts (`LEVY_AMOUNT_A`, `B`, `C`, `D`) for individual items or the `TOTAL_LEVY` in the header, compared to what the GRA system expects.
    *   **Action**: Carefully review the levy calculation logic (Section 6.3) to ensure that each levy is correctly applied to the `UNITYPRICE` and that the sums are accurate.
*   **`A06`**: **INVALID UNITY PRICE**
    *   **Description**: The `UNITYPRICE` provided is invalid (e.g., non-numeric, or outside acceptable range).
    *   **Action**: Ensure `UNITYPRICE` is a valid positive numeric value.
*   **`A07`**: **INVALID DISCOUNT**
    *   **Description**: The discount amount or type is invalid.
    *   **Action**: Validate discount values and types against API specifications.
*   **`A08`**: **INVALID TAXCODE**
    *   **Description**: The `TAXCODE` provided is not one of the accepted values (`A`, `B`, `C`, `D`, `E`).
    *   **Action**: Ensure `TAXCODE` is one of the predefined valid codes.
*   **`A09`**: **INVALID TAXRATE**
    *   **Description**: The `TAXRATE` provided is not one of the accepted values (`0`, `15`, `3`).
    *   **Action**: Ensure `TAXRATE` is one of the predefined valid rates.
*   **`A11`**: **ITEM COUNT NOT A NUMBER**
    *   **Description**: The `ITEMS_COUNTS` field in the header is not a valid numeric value.
    *   **Action**: Ensure `ITEMS_COUNTS` is a valid integer.

### 7.4. TIN Validator Errors
*   **`T01`**: **INVALID TIN NUMBER**
    *   **Description**: The `TIN` provided is not 11 or 15 characters long.
    *   **Action**: Ensure the `TIN` adheres to the specified length requirements.
*   **`T03`**: **TIN NUMBER NOT FOUND**
    *   **Description**: The `TIN` provided is not found in the synchronized GRA data.
    *   **Action**: Verify the `TIN` with the client. It might be an unregistered or incorrect TIN.
*   **`T04`**: **TIN STOPPED**
    *   **Description**: The `TIN` is registered but has been marked as stopped or inactive by GRA.
    *   **Action**: Inform the client to contact GRA regarding the status of their TIN.
*   **`T05`**: **TIN PROTECTED**
    *   **Description**: The `TIN` is protected, implying certain restrictions or special status.
    *   **Action**: Inform the client to contact GRA for details on their TIN status.
*   **`T06`**: **INCORRECT CLIENT TIN PIN**
    *   **Description**: The `CLIENT_TIN_PIN` provided for the TIN is incorrect.
    *   **Action**: Verify the `CLIENT_TIN_PIN` with the client.

### 7.5. System and Processing Errors
*   **`D01`**: **INVOICE ALREADY EXIST**
    *   **Description**: An invoice with the same unique identifier has already been processed by the system.
    *   **Action**: This is similar to `B20`. Ensure uniqueness of invoice numbers.
*   **`D05`**: **INVOICE UNDER STAMPING**
    *   **Description**: The invoice has been received by the VSDC and is currently undergoing the stamping process.
    *   **Action**: This is an informational message. The VCIS should wait and then make a `Signature Request` to retrieve the stamping details.
*   **`D06`**: **STAMPING ENGINE IS DOWN**
    *   **Description**: The VSDC stamping engine is not operational.
    *   **Action**: This indicates a system issue on the GRA side. The VCIS should implement retry mechanisms and potentially alert administrators.
*   **`IS100`**: **INTERNAL ERROR**
    *   **Description**: A generic internal error occurred within the GRA E-VAT system.
    *   **Action**: Implement retry logic. If persistent, contact GRA technical support.
*   **`A13`**: **EVAT NOT ABLE TO REACH ITS DATABASE**
    *   **Description**: The E-VAT system is experiencing database connectivity issues.
    *   **Action**: This indicates a system issue on the GRA side. Implement retry mechanisms and potentially alert administrators.

## 8. Best Practices for Integration
To ensure a smooth, compliant, and robust integration with the GRA E-VAT API, consider the following best practices:

*   **Data Validation**: Implement comprehensive client-side and server-side validation within your VCIS to catch errors before sending requests to the GRA API. This reduces unnecessary API calls and improves efficiency.
*   **Error Handling and Retry Mechanisms**: Design your system to gracefully handle API errors. Implement exponential backoff and retry logic for transient errors (e.g., network issues, temporary service unavailability). Distinguish between transient and permanent errors.
*   **Logging**: Maintain detailed logs of all API requests and responses, including timestamps, request payloads, and response bodies. This is invaluable for troubleshooting, auditing, and dispute resolution.
*   **Idempotency**: Ensure that your system can handle duplicate requests without adverse effects, especially for critical operations like invoice submission. The API's `B20` and `D01` error codes indicate that the system already has some idempotency built-in for invoice numbers.
*   **Asynchronous Processing**: For high-volume systems, consider asynchronous processing of API calls to avoid blocking your primary business operations. This can involve queuing requests and processing responses via webhooks or polling mechanisms.
*   **Security**: Protect your `COMPANY_SECURITY_KEY` with the highest level of security. It should never be exposed in client-side code or publicly accessible logs.
*   **Regular Updates**: Stay informed about any updates or changes to the GRA E-VAT API documentation and specifications. The tax landscape and API versions can evolve.
*   **Testing**: Thoroughly test all integration points in a dedicated test environment before deploying to production. Cover various scenarios, including successful submissions, error conditions, and edge cases.
*   **User Interface Feedback**: Provide clear and informative feedback to end-users within your VCIS regarding the status of E-VAT submissions (e.g., 
invoice successfully submitted, pending stamping, or error encountered).

## 9. Conclusion
Integrating with the GRA E-VAT API requires a meticulous understanding of its technical specifications, data structures, and validation rules. This document has outlined the critical components necessary for a compliant integration, from authentication and data formatting to specific API modules for invoicing, refunds, item management, TIN validation, and reporting. The detailed breakdown of error codes and best practices aims to equip businesses with the knowledge to develop, audit, and maintain a robust E-VAT system.

By adhering to these guidelines, businesses can ensure seamless communication with the GRA E-VAT system, contribute to national tax compliance efforts, and avoid potential penalties associated with non-compliance. Continuous monitoring, thorough testing, and staying updated with any revisions to the GRA API documentation are essential for long-term success in E-VAT integration.

## 10. References
[1] GRA E-VAT API VER 7.0. (n.d.). *Postman*. Retrieved from [https://documenter.getpostman.com/view/20074551/2s8Z76xVYR](https://documenter.getpostman.com/view/20074551/2s8Z76xVYR)
