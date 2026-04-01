/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { PosStore } from '@point_of_sale/app/services/pos_store';

patch(PosStore.prototype, {
    async pay() {
        const currentOrder = this.getOrder();
        await super.pay();
        if (!currentOrder.isRefund) {
            return;
        }

        const refundedOrder = currentOrder.lines[0]?.refunded_orderline_id?.order_id;
        if (!refundedOrder) {
            return;
        }

        const terminalMethods = refundedOrder.payment_ids.filter(
            (paymentLine) => paymentLine.payment_method_id.use_payment_terminal === 'bpos1'
        );
        for (const paymentLine of terminalMethods) {
            const result = currentOrder.addPaymentline(paymentLine.payment_method_id);
            if (!result.status) {
                continue;
            }
            result.data.setAmount(-Math.min(Math.abs(currentOrder.remainingDue), paymentLine.amount));
            result.data.transaction_id = paymentLine.transaction_id;
            result.data.uiState = {
                ...result.data.uiState,
                bpos1_rrn: paymentLine.transaction_id,
            };
        }
    },
});
