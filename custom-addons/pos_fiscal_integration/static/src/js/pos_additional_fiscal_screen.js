/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
export class FiscalIntegrationScreen extends Component {
   static template = "custom_pos_screen.FiscalIntegrationScreen";
   setup() {
       this.pos = usePos();
   }
   closePosIntegrationScreen() {
       const order = this.pos.addNewOrder();
       this.pos.navigate("ProductScreen", {
           orderUuid: order.uuid,
       });
   }

async xReport() {
        try {

            if (!this.pos.config.use_pos_fiscal_service) {
                return;
            }
            console.log("Fiscal service is enabled");

            const pos_fiscal_service_addess = this.pos.config.fiscal_service_ip;
            const pos_fiscal_service_port = this.pos.config.fiscal_service_port;
            const pos_fiscal_service_api_key = this.pos.config.pos_fiscal_service_api_key;

            const response = await fetch(`http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/x-report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': pos_fiscal_service_api_key
                },
            });
            console.log("Fiscal service called:", await response.json());
        } catch (error) {
            console.error("Fiscal service error", error);
        }
    }
}
registry.category("pos_pages").add("FiscalIntegrationScreen", {
   name: "FiscalIntegrationScreen",
   component: FiscalIntegrationScreen,
   route: `/pos/ui/${odoo.pos_config_id}/pos-fiscal-screen`,
   params: {},
});



/*



patch(Navbar.prototype, {
    setup() {
        // call original setup
        this._super?.(...arguments);

        // you can add reactive state if needed
        this.myExtraState = {
            clicked: false,
        };
    },

    async xReport() {
        try {

            if (!this.pos.config.use_pos_fiscal_service) {
                return;
            }
            console.log("Fiscal service is enabled");

            const pos_fiscal_service_addess = this.pos.config.fiscal_service_ip;
            const pos_fiscal_service_port = this.pos.config.fiscal_service_port;
            const pos_fiscal_service_api_key = this.pos.config.pos_fiscal_service_api_key;

            const response = await fetch(`http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/x-report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': pos_fiscal_service_api_key
                },
            });
            console.log("Fiscal service called:", await response.json());
        } catch (error) {
            console.error("Fiscal service error", error);
        }
    },
});

*/