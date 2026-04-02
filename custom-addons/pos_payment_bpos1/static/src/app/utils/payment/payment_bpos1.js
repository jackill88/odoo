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
            const endpoint = isRefund ? '/terminal-refund' : '/terminal-pay';
            const response = await this._callTerminal(endpoint, payload);
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
        const decimals = this.pos.currency.decimal_places ?? 2;
        return {
            amount: Math.abs(line.amount*100),
            amount_minor: 0,
            currency_decimals: decimals,
            ...(isRefund ? this._refundPayloadExtra(line) : {}),
        };
    }

    _refundPayloadExtra(line) {
        const rrn =
            line.uiState?.bpos1_rrn || line.transaction_id || line.payment_ref_no || line.name;
        return rrn ? { original_rrn: rrn } : {};
    }

    async _callTerminal(endpoint, payload) {
        const apiUrl = this.payment_method_id.bpos1_api_url?.trim();
        const apiKey = this.payment_method_id.bpos1_api_key?.trim();
        const merchantIdx = this.payment_method_id.bpos1_merchant_idx;

        if (!apiUrl) {
            throw new Error(_t('The BPOS1 API base URL is not configured.'));
        }
        if (!apiKey) {
            throw new Error(_t('The BPOS1 API key is required.'));
        }

        const normalizedUrl = `${apiUrl.replace(/\/+$/, '')}/${endpoint.replace(/^\/+/, '')}`;
        const headers = {
            'Content-Type': 'application/json',
            'x-api-key': apiKey,
        };
        const body = {
            ...payload,
            ...(merchantIdx != null ? { merchant_idx: merchantIdx } : {}),
        };

        const response = await fetch(normalizedUrl, {
            method: 'POST',
            headers,
            body: JSON.stringify(body),
        });

        const content = await response.text();
        if (!response.ok) {
            const detail = content || response.statusText;
            throw new Error(_t('BPOS1 terminal error: %s', detail));
        }

        if (!content) {
            return {};
        }

        try {
            return JSON.parse(content);
        } catch {
            return { result: content };
        }
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
        const message = error?.message || _t('BPOS1 terminal request failed.');
        this.env.services.dialog.add(AlertDialog, {
            title: _t('BPOS1 Error'),
            body: message,
        });
    }
}

register_payment_method('bpos1', PaymentBpos1);
