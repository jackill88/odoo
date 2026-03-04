## Інтеграція фіскального сервісу для Odoo 19 Point of Sale

Цей модуль додає шар інтеграції між **Odoo 19 Point of Sale** та зовнішнім **локальним фіскальним сервісом** (наприклад, локальним сервісом фіскалізації типу ПРРО, що працює у вашій мережі).

Інтеграція побудована так, що Odoo формує всі фіскальні дані (рядки чека, підсумки, оплати, повернення, рухи готівки, операції відкриття/закриття зміни) і відправляє їх у фіскальний сервіс через HTTP. Фіскальний сервіс відповідає за безпосередню фіскалізацію та повертає в Odoo фіскальний номер чека.

---

### Основні можливості

- **Налаштування фіскального сервісу в конфігурації POS**
  - Нові поля у `pos.config`:
    - **Use POS Fiscal Service Layer** (`use_pos_fiscal_service`)
    - **Fiscal Service API Key** (`pos_fiscal_service_api_key`)
    - **Unique fiscal ID for the POS** (`unique_fiscal_number`)
    - **Fiscal Service IP Address** (`fiscal_service_ip`)
    - **Fiscal Service Port** (`fiscal_service_port`)

- **Фіскальні дані в POS-замовленнях**
  - Нове поле у моделі `pos.order`:
    - **Unique fiscal ID** (`document_fiscal_id`) — зберігає фіскальний номер чека, повернутий фіскальним сервісом (також використовується для повернень).

- **Автоматична фіскалізація чеків**
  - Після підтвердження замовлення в POS модуль:
    - Формує **фіскальний payload** на бекенді (`pos.order.get_fiscal_payload`).
    - Відправляє дані у фіскальний сервіс:
      - `/fiscal-receipt` для звичайних продажів.
      - `/fiscal-receipt-return` для повернень.
    - Зчитує **ReceiptFiscalNumber** з відповіді фіскального сервісу та зберігає його в полі `document_fiscal_id` через маршрут `/pos_fiscal/store_fiscal_id_in_order`.

- **Підтримка повернень**
  - Для замовлень-повернень payload містить:
    - `is_refund = True`
    - `original_receipt_fiscal_id`, що повертається з `get_original_fiscal_id()` оригінального замовлення.

- **Інтеграція рухів готівки**
  - При використанні спливаючого вікна **Cash In/Out** в POS:
    - Для видачі готівки (`type == 'out'`): запит до `/service-output`.
    - Для внесення готівки: запит до `/service-input`.
    - Сума береться зі стану попапу та відправляється у форматі JSON з заголовком `x-api-key`.

- **Інтеграція відкриття/закриття зміни**
  - При підтвердженні **відкриття зміни** в POS:
    - Надсилається POST-запит до `/open-shift`.
  - При підтвердженні **закриття зміни**:
    - Надсилається POST-запит до `/close-shift`.

- **Додатковий екран у POS**
  - Додається нова кнопка **POS-Fiscal** на панелі керування екрану товарів.
  - Відкривається власний екран **Fiscal Integration Screen**, що містить:
    - Кнопку **BACK** для повернення до екрану товарів.
    - Кнопку **Print X Report**, яка викликає `/x-report` у фіскальному сервісі.

---

### Технічний огляд

- **Бекенд (Python)**
  - `models/pos_fiscal_integration_conf.py`
    - Розширює `pos.config` полями для налаштування фіскального сервісу.
  - `models/pos_fiscal_order.py`
    - Розширює `pos.order`:
      - Поле `document_fiscal_id`.
      - `get_fiscal_order_lines()`: формує детальний список товарів (кількість, ціна, ПДВ, знижки).
      - `get_fiscal_payments()`: формує інформацію про оплати (готівка/картка/разом, email тощо).
      - `get_fiscal_payload()`: формує повний payload (товари + оплати, ознаки повернення).
      - `get_original_fiscal_id()`: повертає фіскальний номер оригінального замовлення для повернення.
      - `save_unique_fiscal_id()`: зберігає фіскальний номер чека, повернутий сервісом.
  - `controllers/pos_fiscal_controller.py`
    - JSON-RPC маршрути, які викликаються з фронтенду POS:
      - `/pos_fiscal/get_order_fiscal_payload` → повертає `get_fiscal_payload()` для вказаного замовлення.
      - `/pos_fiscal/store_fiscal_id_in_order` → записує `document_fiscal_id` в замовлення.
      - `/pos_fiscal/get_order_fiscal_id_for_refund` → повертає `get_original_fiscal_id()`.

- **Фронтенд (JavaScript та XML)**
  - `static/src/js/pos_order_payment_validation_patch.js`
    - Патчить `OrderPaymentValidation.afterOrderValidation()`:
      - Викликає бекенд для отримання фіскального payload.
      - Надсилає його у фіскальний сервіс (`/fiscal-receipt` або `/fiscal-receipt-return`).
      - Зберігає повернений фіскальний номер чека в замовлення.
  - `static/src/js/pos_opening_control_patch.js`
    - Патчить `OpeningControlPopup.confirm()` для відправки запиту `/open-shift`.
  - `static/src/js/pos_closing_control_patch.js`
    - Патчить `ClosePosPopup.confirm()` для відправки запиту `/close-shift`.
  - `static/src/js/pos_cash_move_patch.js`
    - Патчить `CashMovePopup.confirm()` для відправки `/service-input` або `/service-output` з сумою готівки.
  - `static/src/js/pos_additional_fiscal_screen.js` + `static/src/xml/pos_additional_fiscal_screen.xml`
    - OWL-екран для фіскальних дій, наразі реалізує X-звіт.
  - `static/src/js/pos_additional_fiscal_screen_button.js` + `static/src/xml/pos_additional_fiscal_screen_button.xml`
    - Додає кнопку **POS-Fiscal** на екран товарів та переходить на фіскальний екран.

---

### Встановлення

- Скопіюйте папку `pos_fiscal_integration` в директорію **addons** або **custom-addons** вашого Odoo 19.
- Оновіть список додатків в Odoo.
- Встановіть модуль **POS Fiscal Integration** через меню Apps.

---

### Налаштування

- Перейдіть до **Point of Sale → Configuration → Point of Sale**.
- Відкрийте конфігурацію потрібного POS.
- У блоці **Fiscal Service Integration**:
  - Увімкніть **Use POS Fiscal Service Layer**.
  - Заповніть **Fiscal Service API Key** (повинен відповідати налаштованому значенню у зовнішньому сервісі).
  - За потреби фіскального сервісу заповніть **Unique fiscal ID for the POS**.
  - Вкажіть **Fiscal Service IP Address** (наприклад, `127.0.0.1` або IP у локальній мережі).
  - Вкажіть **Fiscal Service Port** (наприклад, `8000`).
- Збережіть конфігурацію та відкрийте POS-сесію.

---

### Використання

- **Звичайний продаж**
  - Створіть замовлення в POS та підтвердьте його, як зазвичай.
  - Якщо фіскальний сервіс увімкнено:
    - Модуль відправить фіскальний payload у сервіс.
    - Повернений фіскальний номер чека буде збережено в полі `document_fiscal_id` замовлення.

- **Повернення**
  - Створіть повернення з існуючого замовлення в POS.
  - Після підтвердження повернення:
    - Модуль відправить payload з ознакою повернення та оригінальним фіскальним номером до `/fiscal-receipt-return`.

- **Внесення / видача готівки**
  - Використовуйте стандартні кнопки **Cash In/Out**.
  - Після підтвердження інтеграція відправляє:
    - `/service-input` для внесення готівки.
    - `/service-output` для видачі готівки.

- **Відкриття / закриття зміни**
  - При відкритті POS-сесії та підтвердженні відкриття зміни:
    - Викликається `/open-shift` у фіскальному сервісі.
  - При закритті POS-сесії та підтвердженні закриття зміни:
    - Викликається `/close-shift`.

- **X-звіт**
  - На екрані товарів в POS натисніть кнопку **POS-Fiscal**.
  - На фіскальному екрані натисніть **Print X Report**, щоб викликати `/x-report`.

---

### Вимоги до API фіскального сервісу

Ваш зовнішній фіскальний сервіс повинен:

- Бути доступним по HTTP з пристрою, де запущений POS:
  - `http://<fiscal_service_ip>:<fiscal_service_port>/...`
- Приймати запити з заголовком:
  - `x-api-key: <pos_fiscal_service_api_key>`
- Реалізовувати такі кінцеві точки (використовуються модулем):
  - `POST /fiscal-receipt`
  - `POST /fiscal-receipt-return`
  - `POST /x-report`
  - `POST /open-shift`
  - `POST /close-shift`
  - `POST /service-input`
  - `POST /service-output`
- Для чеків продажу та повернення відповідати JSON-структурою, що містить:
  - `result.prro_data.Values.ReceiptFiscalNumber`  
    — це значення використовується як `document_fiscal_id` в Odoo.

---

### Примітки та обмеження

- Цей модуль **не реалізує** фіскальну логіку самостійно; він лише:
  - Формує дані.
  - Відправляє їх у зовнішній фіскальний сервіс.
  - Зберігає повернений фіскальний номер.
- Вся логіка фіскалізації, обробка помилок, збереження даних та відповідність законодавчим вимогам лежить на стороні вашого зовнішнього фіскального сервісу.


