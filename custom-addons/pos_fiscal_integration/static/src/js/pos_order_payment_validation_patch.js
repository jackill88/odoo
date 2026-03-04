/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { logPosMessage } from "@point_of_sale/app/utils/pretty_console_log";
export const CONSOLE_COLOR = "#F5B427";



async function getFiscalPayload(order) {
    // get the serialized data for order ID from the backend
    const payload = await rpc("/pos_fiscal/get_order_fiscal_payload", {
        order_id: order.id, 
    });
    return payload
}

patch(OrderPaymentValidation.prototype, {
    async afterOrderValidation() {
        // Call original method first
        await super.afterOrderValidation(); 

        if (!this.pos.config.use_pos_fiscal_service) {
            return;
        }
        console.log("Fiscal service is enabled. Sending receipt data to the service...");

        const pos_fiscal_service_addess = this.pos.config.fiscal_service_ip;
        const pos_fiscal_service_port = this.pos.config.fiscal_service_port;
        const pos_fiscal_service_api_key = this.pos.config.pos_fiscal_service_api_key;

        // get order data -- the model is here
        // order: addons/point_of_sale/static/src/app/models/pos_order.js
        // order line: addons/point_of_sale/static/src/app/models/pos_order_line.js
        // product: addons/point_of_sale/static/src/app/models/product_product.js
        const order = this.pos.getOrder();
        // get serialized data
        const fiscal_payload = await getFiscalPayload(order);
        // get the is_refund flag
        const is_refund = fiscal_payload.is_refund;

        if (is_refund) {
            logPosMessage(
                "Store",
                "OrderPaymentValidation - afterOrderValidation() (patched)",
                "POS Fiscal integration: refund detected. Will send refund data to the service",
                CONSOLE_COLOR
            );
        }
        else {
            logPosMessage(
                "Store",
                "OrderPaymentValidation - afterOrderValidation() (patched)",
                "POS Fiscal integration: will send receipt data to fiscal service",
                CONSOLE_COLOR
            );
        };


        try {

            let pos_result;

            if (is_refund) {
                pos_result = await fetch(`http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/fiscal-receipt-return`,
                    {   method: 'POST',
                         headers: {
                            'Content-Type': 'application/json',
                            'x-api-key': pos_fiscal_service_api_key
                        },
                        body: JSON.stringify(fiscal_payload)
                    });

            }
            else {
                pos_result = await fetch(`http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/fiscal-receipt`,
                    {   method: 'POST',
                         headers: {
                            'Content-Type': 'application/json',
                            'x-api-key': pos_fiscal_service_api_key
                        },
                        body: JSON.stringify(fiscal_payload)
                    });
            };

            // Check HTTP status
            if (!pos_result.ok) {
                // pos_result.ok is true if status is 200–299
                throw new Error(`Fiscal service error: ${pos_result.status} ${pos_result.statusText}`);
            }

            // Parse JSON body
            const data = await pos_result.json();

            // Access ReceiptFiscalNum
            const fiscal_num = data.result.prro_data.Values.ReceiptFiscalNumber;

            //store it in document_fiscal_id
            const order_update_res = await rpc("/pos_fiscal/store_fiscal_id_in_order", {
                order_id: order.id, 
                document_fiscal_id: fiscal_num
            });   
            if (!order_update_res) {
                throw new Error(`Fiscal service error: couldn't update fiscal number in the order`);
            }         
            
            console.log("POS Fiscal integration: successfully sent receipt data");
        } catch (error) {
            console.error("POS Fiscal integration: failed to send receipt data", error);
        }

    }
});