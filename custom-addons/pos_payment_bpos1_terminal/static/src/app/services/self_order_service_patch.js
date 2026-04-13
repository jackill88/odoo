/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { SelfOrder } from '@pos_self_order/app/services/self_order_service';

patch(SelfOrder.prototype, {

    filterPaymentMethods(pms) {
        const filtered =  super.filterPaymentMethods(pms);

        if (this.config.self_ordering_mode === "kiosk") {
            const extra = pms.filter(
                (rec) => rec.use_payment_terminal === "bpos1_terminal"
            );

            // Merge + avoid duplicates
            return [...new Set([...filtered, ...extra])];
        }

        return filtered
    }

    ,
});


