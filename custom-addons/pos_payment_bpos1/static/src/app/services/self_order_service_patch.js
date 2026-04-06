/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { SelfOrder } from '@pos_self_order/app/services/self_order_service';

patch(SelfOrder.prototype, {
    initProducts() {
        this.config.iface_available_categ_ids = this.config.iface_available_categ_ids || [];
        return super.initProducts(...arguments);
    },

    _initLanguages() {
        this.config.self_ordering_available_language_ids =
            this.config.self_ordering_available_language_ids || [];
        return super._initLanguages(...arguments);
    },

    async setup(...args) {
        const result = await super.setup(...args);
        if (this.config && !this.config.currency_id) {
            this.config.currency_id = this.company?.currency_id;
        }
        return result;
    },

    hasPaymentMethod() {
        if (this.config.self_ordering_mode !== 'kiosk') {
            return super.hasPaymentMethod?.() ?? true;
        }
        const terminalWhitelist = new Set(['adyen', 'stripe', 'emulator', 'bpos1']);
        return this.models['pos.payment.method']
            .getAll()
            .some((rec) => terminalWhitelist.has(rec.use_payment_terminal));
    },
});
