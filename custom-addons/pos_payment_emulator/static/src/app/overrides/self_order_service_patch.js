/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SelfOrder } from "@pos_self_order/app/services/self_order_service";

patch(SelfOrder.prototype, {
    /**
     * Extend kiosk payment method filtering to include the emulator terminal.
     *
     * Keeps the original behavior (Adyen, Stripe, etc.) and adds any
     * payment methods configured with use_payment_terminal = 'emulator'.
     */
    filterPaymentMethods(pms) {
        const methods = super.filterPaymentMethods(pms) || [];

        if (this.config.self_ordering_mode !== "kiosk") {
            return methods;
        }

        const terminalMethods = pms.filter((rec) =>
            ["emulator", "bpos1"].includes(rec.use_payment_terminal)
        );
        const existingIds = new Set(methods.map((m) => m.id));

        for (const pm of terminalMethods) {
            if (!existingIds.has(pm.id)) {
                methods.push(pm);
            }
        }

        return methods;
    },
});
