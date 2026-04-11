/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';
import { PaymentScreen } from '@point_of_sale/app/screens/payment_screen/payment_screen';
import { PaymentScreenBpos1TerminalPanel } from '../../components/bpos1_terminal_panel/bpos1_terminal_panel';

patch(PaymentScreen, {
    components: {
        ...PaymentScreen.components,
        PaymentScreenBpos1TerminalPanel,
    },
});

patch(PaymentScreen.prototype, {
    async addNewPaymentLine(paymentMethod) {
        if (
            paymentMethod.use_payment_terminal === 'bpos1_terminal' &&
            this.isRefundOrder
        ) {
            const refundedOrder = this.currentOrder.lines[0]?.refunded_orderline_id?.order_id;
            if (!refundedOrder) {
                return false;
            }

            const existingTransactions = new Set(
                this.currentOrder.payment_ids.map((pi) => pi.transaction_id).filter(Boolean)
            );
            const originalLine = refundedOrder.payment_ids.find(
                (pi) =>
                    pi.payment_method_id.use_payment_terminal === 'bpos1_terminal' &&
                    pi.transaction_id &&
                    !existingTransactions.has(pi.transaction_id)
            );

            if (!originalLine) {
                this.pos.notification.add(
                    _t('No terminal payment from the original order is available for refunding.'),
                    { type: 'warning', sticky: false }
                );
                return false;
            }

            const result = await super.addNewPaymentLine(paymentMethod);
            if (result) {
                const newPaymentLine = this.paymentLines.at(-1);
                newPaymentLine.updateRefundPaymentLine(originalLine);
            }
            return result;
        }
        return await super.addNewPaymentLine(paymentMethod);
    },
});
