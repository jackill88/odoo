/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

import { ConfirmationPage } from "@pos_self_order/app/pages/confirmation_page/confirmation_page";
import { logPosMessage } from "@point_of_sale/app/utils/pretty_console_log";
export const CONSOLE_COLOR = "#F5B427";

async function getFiscalPayload(order) {
    // get the serialized data for order ID from the backend
    const payload = await rpc("/pos_fiscal/get_order_fiscal_payload", {
        order_id: order.id, 
    });
    return payload
}


patch(ConfirmationPage.prototype, {
    async beforePrintOrder() {
        // no need to call original method first as it meant to be overriden.

        if (!this.selfOrder.config.use_pos_fiscal_service) {
            return;
        }
        else {
            console.log("Fiscal service is enabled. Sending receipt data to the service...");

            const pos_fiscal_service_addess = this.selfOrder.config.fiscal_service_ip;
            const pos_fiscal_service_port = this.selfOrder.config.fiscal_service_port;
            const pos_fiscal_service_api_key = this.selfOrder.config.pos_fiscal_service_api_key;
            const controller = new AbortController();
            const timeoutMs = 5000; // 5 seconds
            
            const timeout = setTimeout(() => controller.abort(), timeoutMs);
        

            if (this.selfOrder.config.self_ordering_mode === "kiosk" ) {
                const fiscal_order = this.confirmedOrder;
                const fiscal_payload = await getFiscalPayload(fiscal_order);

                logPosMessage(
                    "Store",
                    "ConfirmationPage - printOrder() (patched)",
                    "POS Fiscal integration: (kiosk mode)will send receipt data to fiscal service",
                    CONSOLE_COLOR
                );

                try {

                    let pos_result;
        
                    pos_result = await fetch(`http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/fiscal-receipt`,
                        {   method: 'POST',
                                headers: {
                                'Content-Type': 'application/json',
                                'x-api-key': pos_fiscal_service_api_key
                            },
                            body: JSON.stringify(fiscal_payload)
                        });

                    // check for timeout
                    clearTimeout(timeout);

        
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
                        order_id: fiscal_order.id, 
                        document_fiscal_id: fiscal_num
                    });   
                    if (!order_update_res) {
                        throw new Error(`Fiscal service error: couldn't update fiscal number in the order`);
                    }         
                    
                    console.log("POS Fiscal integration: successfully sent receipt data");

                    return true;
                } catch (error) {
                    this.selfOrder.handleErrorNotification("Fiscal service request timed out");
                    this.selfOrder.paymentError = true;
                    if (error.name === "AbortError") {
                        console.error("Fiscal service request timed out");
                        return false;
                    } else {
                        console.error("POS Fiscal integration: failed to send receipt data", error);
                        return false;
                    }
                }

        }

    }
},
});