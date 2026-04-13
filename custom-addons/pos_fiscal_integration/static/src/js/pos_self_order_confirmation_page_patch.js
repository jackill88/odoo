/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

import { ConfirmationPage } from "@pos_self_order/app/pages/confirmation_page/confirmation_page";
import { logPosMessage } from "@point_of_sale/app/utils/pretty_console_log";
export const CONSOLE_COLOR = "#F5B427";

const POS_FISCAL_PAYLOAD_ROUTE = "/pos_fiscal/get_order_fiscal_payload";
const POS_FISCAL_PAYLOAD_PUBLIC_ROUTE = "/pos_fiscal/get_order_fiscal_payload_public";
const POS_FISCAL_STORE_ROUTE = "/pos_fiscal/store_fiscal_id_in_order";
const POS_FISCAL_STORE_PUBLIC_ROUTE = "/pos_fiscal/store_fiscal_id_in_order_public";

async function getFiscalPayload(order, accessToken = null) {
    const route = accessToken ? POS_FISCAL_PAYLOAD_PUBLIC_ROUTE : POS_FISCAL_PAYLOAD_ROUTE;
    const params = { order_id: order.id };
    if (accessToken) {
        params.access_token = accessToken;
    }
    const payload = await rpc(route, params);
    return payload;
}

async function storeFiscalId(orderId, documentFiscalId, accessToken = null) {
    const route = accessToken ? POS_FISCAL_STORE_PUBLIC_ROUTE : POS_FISCAL_STORE_ROUTE;
    const params = {
        order_id: orderId,
        document_fiscal_id: documentFiscalId,
    };
    if (accessToken) {
        params.access_token = accessToken;
    }
    return rpc(route, params);
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
            const timeoutMs = 60000; // 1 minute
            
            const timeout = setTimeout(() => controller.abort(), timeoutMs);
        

            if (this.selfOrder.config.self_ordering_mode === "kiosk" ) {
                const fiscal_order = this.confirmedOrder;
                const fiscal_payload = await getFiscalPayload(fiscal_order, fiscal_order.access_token);

                logPosMessage(
                    "Store",
                    "ConfirmationPage - printOrder() (patched)",
                    "POS Fiscal integration: (kiosk mode) will send receipt data to fiscal service",
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
                        let errorDetail = pos_result.statusText;

                        try {
                            const errorJson = await pos_result.json();
                            errorDetail = errorJson.detail || JSON.stringify(errorJson);
                        } catch {
                            // response is not JSON
                            const text = await pos_result.text();
                            if (text) errorDetail = text;
                        }

                        throw new Error(`Fiscal service error: ${pos_result.status} ${errorDetail}`);
                    }
        
                    // Parse JSON body
                    const data = await pos_result.json();
        
                    // Access ReceiptFiscalNum
                    const fiscal_num = data.result.prro_data.Values.ReceiptFiscalNumber;
        
                    //store it in document_fiscal_id
                    const order_update_res = await storeFiscalId(
                        fiscal_order.id,
                        fiscal_num,
                        fiscal_order.access_token
                    );   
                    if (!order_update_res) {
                        throw new Error(`Fiscal service error: couldn't update fiscal number in the order`);
                    }         
                    
                    console.log("POS Fiscal integration: successfully sent receipt data");

                    return true;
                } catch (error) {
                    this.selfOrder.paymentError = true;
                    if (error.name === "AbortError") {
                        this.selfOrder.handleErrorNotification("Fiscal service request timed out");
                        console.error("Fiscal service request timed out");
                        return false;
                    } else {
                        this.selfOrder.handleErrorNotification(`POS Fiscal integration: failed to send receipt data: ${error}`);
                        console.error("POS Fiscal integration: failed to send receipt data", error);
                        return false;
                    }
                }

        }

    }
},
});
