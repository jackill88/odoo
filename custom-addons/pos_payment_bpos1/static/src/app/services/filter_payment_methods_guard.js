/** @odoo-module **/

import { registerSelfOrderTerminalFilter } from '@pos_self_order_terminal_registry/app/services/self_order_terminal_registry';

registerSelfOrderTerminalFilter((selfOrder, safePms) => {
    if (selfOrder.config._self_order_pos !== true) {
        return [];
    }
    return Array.isArray(safePms)
        ? safePms.filter((method) => method.use_payment_terminal === 'bpos1')
        : [];
});
