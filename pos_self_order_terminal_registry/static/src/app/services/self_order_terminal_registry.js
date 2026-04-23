/** @odoo-module **/

const terminalFilters = [];

export function registerSelfOrderTerminalFilter(filterFn) {
    if (typeof filterFn === 'function') {
        terminalFilters.push(filterFn);
    }
}

export function applySelfOrderTerminalFilters(selfOrder, safePaymentMethods) {
    if (!terminalFilters.length) {
        return [];
    }
    const safePms = Array.isArray(safePaymentMethods) ? safePaymentMethods : [];
    const collected = [];

    for (const filterFn of terminalFilters) {
        try {
            const filterResult = filterFn(selfOrder, safePms);
            if (Array.isArray(filterResult)) {
                collected.push(...filterResult);
            }
        } catch (error) {
            console.error('self_order_terminal_registry filter failed', error);
        }
    }

    const unique = new Map();
    for (const method of collected) {
        if (method?.id) {
            unique.set(method.id, method);
        }
    }
    return Array.from(unique.values());
}
