/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import { logPosMessage } from "@point_of_sale/app/utils/pretty_console_log";
export const CONSOLE_COLOR = "#F5B427";

patch(ClosePosPopup.prototype, {
    async confirm() {
        // Call original method first
        await super.confirm(...arguments);

        if (!this.pos.config.use_pos_fiscal_service) {
            return;
        }
        console.log("Fiscal service is enabled");

        const pos_fiscal_service_addess = this.pos.config.fiscal_service_ip;
        const pos_fiscal_service_port = this.pos.config.fiscal_service_port;
        const pos_fiscal_service_api_key = this.pos.config.pos_fiscal_service_api_key;

        logPosMessage(
            "Store",
            "ClosePosPopup - confirm() (patched)",
            "POS Fiscal integration: will send data to fiscal service to close the shift",
            CONSOLE_COLOR
        );


        try {
            await fetch(`http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/close-shift`,
                    {   method: 'POST',
                         headers: {
                            'Content-Type': 'application/json',
                            'x-api-key': pos_fiscal_service_api_key
                        }
                    });

            console.log("Fiscal close shift sent");
        } catch (error) {
            console.error("Fiscal close shift failed", error);
        }
    },
});

