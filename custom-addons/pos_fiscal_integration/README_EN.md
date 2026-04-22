## POS Fiscal Integration for Odoo 19 Point of Sale

This module adds an integration layer between **Odoo 19 Point of Sale** and an external **local fiscal service** (for example, a PRRO-like fiscalization service running in your local network).

The integration is designed so that Odoo prepares all fiscal data (receipt lines, totals, payments, refunds, cash in/out, shift operations) and sends it to the fiscal service via HTTP. The fiscal service is responsible for the actual fiscalization and for returning the fiscal receipt number back to Odoo.

---

### Main Features

- **POS configuration for fiscal service**
  - New fields on `pos.config`:
    - **Use POS Fiscal Service Layer** (`use_pos_fiscal_service`)
    - **Fiscal Service API Key** (`pos_fiscal_service_api_key`)
    - **Unique fiscal ID for the POS** (`unique_fiscal_number`)
    - **Fiscal Service IP Address** (`fiscal_service_ip`)
    - **Fiscal Service Port** (`fiscal_service_port`)

- **Fiscal data on POS orders**
  - New field on `pos.order`:
    - **Unique fiscal ID** (`document_fiscal_id`) used to store the fiscal receipt number returned by the fiscal service (also used for refunds).

- **Automatic fiscalization of receipts**
  - After a POS order is validated, the module:
    - Builds a **fiscal payload** on the backend (`pos.order.get_fiscal_payload`).
    - Sends the data to the fiscal service:
      - `/fiscal-receipt` for normal sales.
      - `/fiscal-receipt-return` for refunds.
    - Reads the **ReceiptFiscalNumber** from the response and stores it in `document_fiscal_id` via `/pos_fiscal/store_fiscal_id_in_order`.

- **Refund support**
  - For refund orders, the payload contains:
    - `is_refund = True`
    - `original_receipt_fiscal_id` returned from `get_original_fiscal_id()` of the original order.

- **Cash operations integration**
  - When using the **Cash In/Out** popup in POS:
    - For cash out (`type == 'out'`): sends to `/service-output`.
    - For cash in: sends to `/service-input`.
    - Amount is taken from the popup state and sent as JSON with header `x-api-key`.

- **Shift open/close integration**
  - On POS **opening control** confirmation:
    - Sends a POST request to `/open-shift`.
  - On POS **closing control** confirmation:
    - Sends a POST request to `/close-shift`.

- **Additional POS screen**
  - Adds a new **POS-Fiscal** button on the Product Screen toolbar.
  - Opens a custom **Fiscal Integration Screen** with:
    - A **BACK** button to return to the product screen.
    - A **Print X Report** button calling `/x-report` on the fiscal service.

---

### Technical Overview

- **Backend (Python)**
  - `models/pos_fiscal_integration_conf.py`
    - Extends `pos.config` with fiscal settings fields.
  - `models/pos_fiscal_order.py`
    - Extends `pos.order` with:
      - `document_fiscal_id` field.
      - `get_fiscal_order_lines()`: builds detailed goods list (quantities, prices, VAT, discounts).
      - `get_fiscal_payments()`: builds payments info (cash/card/total, email, etc.).
      - `get_fiscal_payload()`: builds the complete payload (goods + payments, refund flags).
      - `get_original_fiscal_id()`: returns fiscal ID of original order for refunds.
      - `save_unique_fiscal_id()`: stores returned fiscal receipt number.
  - `controllers/pos_fiscal_controller.py`
    - JSON-RPC routes used from the POS frontend:
      - `/pos_fiscal/get_order_fiscal_payload` → returns `get_fiscal_payload()` for a given order.
      - `/pos_fiscal/store_fiscal_id_in_order` → writes `document_fiscal_id` to the order.
      - `/pos_fiscal/get_order_fiscal_id_for_refund` → returns `get_original_fiscal_id()`.

- **Frontend (JavaScript & XML)**
  - `static/src/js/pos_order_payment_validation_patch.js`
    - Patches `OrderPaymentValidation.afterOrderValidation()` to:
      - Call the backend to get the fiscal payload.
      - POST it to the fiscal service (`/fiscal-receipt` or `/fiscal-receipt-return`).
      - Store the returned fiscal receipt number in the order.
  - `static/src/js/pos_opening_control_patch.js`
    - Patches `OpeningControlPopup.confirm()` to send `/open-shift`.
  - `static/src/js/pos_closing_control_patch.js`
    - Patches `ClosePosPopup.confirm()` to send `/close-shift`.
  - `static/src/js/pos_cash_move_patch.js`
    - Patches `CashMovePopup.confirm()` to send `/service-input` or `/service-output` with the cash amount.
  - `static/src/js/pos_additional_fiscal_screen.js` + `static/src/xml/pos_additional_fiscal_screen.xml`
    - OWL screen for fiscal actions, currently providing X Report.
  - `static/src/js/pos_additional_fiscal_screen_button.js` + `static/src/xml/pos_additional_fiscal_screen_button.xml`
    - Adds a **POS-Fiscal** button to the Product Screen and navigates to the fiscal screen.

---

### Installation

- Copy the `pos_fiscal_integration` folder into your Odoo 19 **addons** or **custom-addons** directory.
- Update the app list in Odoo.
- Install the **POS Fiscal Integration** module from the Apps menu.

---

### Configuration

- Go to **Point of Sale → Configuration → Point of Sale**.
- Open the POS configuration you want to integrate.
- In the **Fiscal Service Integration** section:
  - Enable **Use POS Fiscal Service Layer**.
  - Set **Fiscal Service API Key** (must match the external service configuration).
  - Set **Unique fiscal ID for the POS** if required by the fiscal service.
  - Set **Fiscal Service IP Address** (e.g. `127.0.0.1` or LAN IP).
  - Set **Fiscal Service Port** (e.g. `8000`).
- Save the configuration and open the POS session.

---

### Usage

- **Normal sale**
  - Create an order in POS and validate it as usual.
  - If the fiscal service is enabled:
    - The module sends the fiscal payload to the service.
    - The returned fiscal receipt number is stored on the order (`document_fiscal_id`).

- **Refund**
  - Create a refund from an existing order in POS.
  - When the refund is validated:
    - The module sends the refund payload with the original fiscal ID to `/fiscal-receipt-return`.

- **Cash in / Cash out**
  - Use the standard **Cash In/Out** buttons.
  - After confirmation, the integration sends:
    - `/service-input` for cash in.
    - `/service-output` for cash out.

- **Open / Close shift**
  - When opening a POS session and confirming the opening control:
    - `/open-shift` is called on the fiscal service.
  - When closing a POS session and confirming the closing control:
    - `/close-shift` is called.

- **X Report**
  - In the POS Product Screen, press the **POS-Fiscal** button.
  - On the fiscal screen, click **Print X Report** to trigger `/x-report`.

---

### Fiscal Service API Expectations

Your external fiscal service is expected to:

- Be accessible via HTTP from the POS device:
  - `http://<fiscal_service_ip>:<fiscal_service_port>/...`
- Accept requests with header:
  - `x-api-key: <pos_fiscal_service_api_key>`
- Implement the following endpoints (as used in this module):
  - `POST /fiscal-receipt`
  - `POST /fiscal-receipt-return`
  - `POST /x-report`
  - `POST /open-shift`
  - `POST /close-shift`
  - `POST /service-input`
  - `POST /service-output`
- For fiscal receipts and refunds, respond with JSON containing:
  - `result.prro_data.Values.ReceiptFiscalNumber`  
    which is used as the `document_fiscal_id` in Odoo.

---

### Notes and Limitations

- This module does **not** implement any fiscal logic itself; it only:
  - Prepares data.
  - Sends it to the external fiscal service.
  - Stores the returned fiscal number.
- The actual fiscalization process, error handling, storage, and compliance are the responsibility of your external fiscal service.


