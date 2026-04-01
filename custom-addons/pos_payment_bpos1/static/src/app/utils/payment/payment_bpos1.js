/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { AlertDialog } from '@web/core/confirmation_dialog/confirmation_dialog';
import { PaymentInterface } from '@point_of_sale/app/utils/payment/payment_interface';
import { register_payment_method } from '@point_of_sale/app/services/pos_store';

const RRN_KEYS = ['rrn', 'RRN', 'referenceNumber', 'reference_number', 'terminal_rrn'];

export class PaymentBpos1 extends PaymentInterface {
    async sendPaymentRequest(uuid) {
        const line = this.pos.getOrder().getPaymentlineByUuid(uuid);
        if (!line) {
            return false;
        }
        const isRefund = line.amount < 0;
        const payload = this._buildPayload(line, isRefund);
        line.setPaymentStatus('waitingCard');
        try {
            const method = isRefund ? 'bpos1_send_refund_request' : 'bpos1_send_payment_request';
            const response = await this._callBackend(method, payload);
            this._handleSuccess(line, response);
            return true;
        } catch (error) {
            this._handleError(line, error);
            return false;
        }
    }

    sendPaymentCancel() {
        return Promise.resolve(true);
    }

    _buildPayload(line, isRefund) {
        const decimals = this.pos.currency.decimal_places || 2;
        const amountMinor = Math.round(Math.abs(line.amount) * Math.pow(10, decimals));
        return {
            amount: Math.abs(line.amount),
            amount_minor: amountMinor,
            currency_decimals: decimals,
            ...(isRefund ? this._refundPayloadExtra(line) : {}),
        };
    }

    _refundPayloadExtra(line) {
        const rrn =
            line.uiState?.bpos1_rrn || line.transaction_id || line.payment_ref_no || line.name;
        return rrn ? { original_rrn: rrn } : {};
    }

    _callBackend(method, payload) {
        return this.env.services.orm.silent.call('pos.payment.method', method, [
            [this.payment_method_id.id],
            payload,
        ]);
    }

    _handleSuccess(line, response) {
        const rrn = this._extractRrn(response);
        if (rrn) {
            line.transaction_id = rrn;
            line.uiState = {
                ...line.uiState,
                bpos1_rrn: rrn,
            };
        }
        line.setPaymentStatus('done');
    }

    _extractRrn(response) {
        if (!response) {
            return null;
        }
        for (const key of RRN_KEYS) {
            if (response[key]) {
                return response[key];
            }
        }
        return null;
    }

    _handleError(line, error) {
        line.setPaymentStatus('retry');
        const message =
            error?.data?.message ||
            error?.data?.error ||
            error?.message ||
            _t('BPOS1 terminal request failed.');
        this.env.services.dialog.add(AlertDialog, {
            title: _t('BPOS1 Error'),
            body: message,
        });
    }
}

register_payment_method('bpos1', PaymentBpos1);
