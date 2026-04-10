/** @odoo-module **/

import { PosPayment } from '@point_of_sale/app/models/pos_payment';
import { patch } from '@web/core/utils/patch';

patch(PosPayment.prototype, {
    setup(vals) {
        super.setup(vals);
        this.uiState = {
            ...(this.uiState ?? {}),
            bpos1_rrn: null,
        };
    },

    updateRefundPaymentLine(refundedPaymentLine) {
        super.updateRefundPaymentLine(refundedPaymentLine);
        if (refundedPaymentLine?.transaction_id) {
            this.uiState = {
                ...this.uiState,
                bpos1_rrn: refundedPaymentLine.transaction_id,
            };
        }
    },
});
