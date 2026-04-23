/** @odoo-module */

import { patch } from '@web/core/utils/patch';
import { PaymentForm } from '@payment/interactions/payment_form';
import { rpc } from '@web/core/network/rpc';

patch(PaymentForm.prototype, {

    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'emulator') {
            await super._prepareInlineForm(...arguments);
            return;
        }
        if (flow === 'token') {
            return;
        }
        this._setPaymentFlow('direct');
    },

    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'emulator') {
            await super._processDirectFlow(...arguments);
            return;
        }
        await rpc('/payment/emulator/simulate', {
            reference: processingValues.reference,
            simulated_state: 'done',
        });
        window.location = '/payment/status';
    },
});
