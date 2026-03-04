/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CashMovePopup } from "@point_of_sale/app/components/popups/cash_move_popup/cash_move_popup";
import { logPosMessage } from "@point_of_sale/app/utils/pretty_console_log";
export const CONSOLE_COLOR = "#F5B427";


patch(CashMovePopup.prototype, {
    async confirm() {
        // Call original method first
        await super.confirm(); 

        if (!this.pos.config.use_pos_fiscal_service) {
            return;
        }
        console.log("Fiscal service is enabled. Sending cash move data to the service...");


        const pos_fiscal_service_addess = this.pos.config.fiscal_service_ip;
        const pos_fiscal_service_port = this.pos.config.fiscal_service_port;
        const pos_fiscal_service_api_key = this.pos.config.pos_fiscal_service_api_key;

        logPosMessage(
            "Store",
            "CashMovePopup - confirm() (patched)",
            "POS Fiscal integration: will send data to fiscal service",
            CONSOLE_COLOR
        );

        let pos_result;
        const fiscal_amount = parseFloat(this.state.amount).toFixed(2);
        const cash_move_type = this.state.type;
        const cash_move_fiscal_payload = {'amount': fiscal_amount};

        try {
            
            if (cash_move_type == 'out') {
                pos_result = await fetch(`http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/service-output`,
                    {   method: 'POST',
                            headers: {
                            'Content-Type': 'application/json',
                            'x-api-key': pos_fiscal_service_api_key
                        },
                        body: JSON.stringify(cash_move_fiscal_payload)
                    });           
                }
            else {
                pos_result = await fetch(`http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/service-input`,
                    {   method: 'POST',
                            headers: {
                            'Content-Type': 'application/json',
                            'x-api-key': pos_fiscal_service_api_key
                        },
                        body: JSON.stringify(cash_move_fiscal_payload)
                    });
            };

            // Check HTTP status
            if (!pos_result.ok) {
                // pos_result.ok is true if status is 200–299
                throw new Error(`Fiscal service error: ${pos_result.status} ${pos_result.statusText}`);
            }

        } 
        catch (error) {
            console.error("POS Fiscal integration: failed to send receipt data", error);
        }
    }

});