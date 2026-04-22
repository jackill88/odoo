/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { SelfOrder } from '@pos_self_order/app/services/self_order_service';
import { applySelfOrderTerminalFilters } from '../services/self_order_terminal_registry';

patch(SelfOrder.prototype, {
    filterPaymentMethods(pms, ...args) {
        const safePms = Array.isArray(pms)
            ? pms
            : this.models['pos.payment.method']?.getAll() ?? [];
        const baseMethods = super.filterPaymentMethods?.(safePms, ...args) ?? [];
        const extraMethods = applySelfOrderTerminalFilters(this, safePms);

        if (!extraMethods.length) {
            return baseMethods;
        }

        const existingIds = new Set(baseMethods.map((method) => method.id));
        const mergedMethods = [...baseMethods];
        for (const method of extraMethods) {
            if (!method || existingIds.has(method.id)) {
                continue;
            }
            mergedMethods.push(method);
            existingIds.add(method.id);
        }
        return mergedMethods;
    },
});
