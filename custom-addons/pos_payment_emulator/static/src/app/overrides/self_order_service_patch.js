/** @odoo-module **/

import { registerSelfOrderTerminalFilter } from "@pos_self_order_terminal_registry/static/src/app/services/self_order_terminal_registry";

registerSelfOrderTerminalFilter((selfOrder, safePms) => {
    if (selfOrder.config?.self_ordering_mode !== "kiosk") {
        return [];
    }
    return Array.isArray(safePms)
        ? safePms.filter((rec) => ["emulator", "bpos1"].includes(rec.use_payment_terminal))
        : [];
});
