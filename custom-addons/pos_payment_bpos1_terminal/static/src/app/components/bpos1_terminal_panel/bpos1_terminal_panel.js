/** @odoo-module **/

import { Component } from '@odoo/owl';
import { _t } from '@web/core/l10n/translation';

export class PaymentScreenBpos1TerminalPanel extends Component {
    static template = 'pos_payment_bpos1_terminal.PaymentScreenBpos1TerminalPanel';
    static props = {
        selectedPaymentLine: { type: Object, optional: true },
        order: { type: Object, optional: true },
    };

    get terminalPaymentMethod() {
        const line = this.props.selectedPaymentLine;
        if (!line) {
            return null;
        }
        const method = line.payment_method_id;
        return method?.use_payment_terminal === 'bpos1_terminal' ? method : null;
    }

    get hasTerminalLine() {
        return Boolean(this.terminalPaymentMethod);
    }

    get formattedAmount() {
        if (!this.hasTerminalLine) {
            return '';
        }
        const amount = this.props.selectedPaymentLine?.amount ?? 0;
        return this.env.utils.formatCurrency(Math.abs(amount));
    }

    get terminalMerchantId() {
        return this.terminalPaymentMethod?.bpos1_terminal_merchant_id || _t('Not configured');
    }

    get panelDescription() {
        return _t('Integrates BPOS1-compatible POS terminals with this system.');
    }

    get orderRemaining() {
        if (!this.props.order) {
            return '';
        }
        return this.env.utils.formatCurrency(this.props.order.remainingDue);
    }
}
