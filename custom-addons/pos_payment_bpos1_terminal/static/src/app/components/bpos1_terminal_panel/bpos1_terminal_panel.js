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

    get terminalDeviceId() {
        return this.terminalPaymentMethod?.bpos1_terminal_device_id || _t('Not configured');
    }

    get terminalStoreCode() {
        return this.terminalPaymentMethod?.bpos1_terminal_store_code || _t('Not configured');
    }

    get terminalToken() {
        return this.terminalPaymentMethod?.bpos1_terminal_token || _t('Not configured');
    }

    get terminalSecretStatus() {
        return this.terminalPaymentMethod?.bpos1_terminal_secret ? _t('Stored') : _t('Not set');
    }

    get panelDescription() {
        return _t('Bakong KHQR is currently running in stub mode and auto-validates the payment without contacting a terminal.');
    }

    get orderRemaining() {
        if (!this.props.order) {
            return '';
        }
        return this.env.utils.formatCurrency(this.props.order.remainingDue);
    }
}
