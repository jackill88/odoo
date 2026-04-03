/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { AlertDialog } from '@web/core/confirmation_dialog/confirmation_dialog';
import { PaymentInterface } from '@point_of_sale/app/utils/payment/payment_interface';
import { register_payment_method } from '@point_of_sale/app/services/pos_store';

const RRN_KEYS = ['rrn', 'RRN', 'referenceNumber', 'reference_number', 'terminal_rrn'];

function getTerminalData(response) {
    return response?.result ?? response ?? {};
}

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
        const amount = Math.abs(Math.round(line.amount * 100));
        return {
            amount: amount,
            amount_minor: 0,
            currency_decimals: decimals,
            ...(isRefund ? this._refundPayloadExtra(line) : {}),
        };
    }

    _refundPayloadExtra(line) {
        const rrn = line.uiState?.bpos1_rrn || line.transaction_id || line.payment_ref_no || line.name;
        return rrn ? { original_rrn: rrn } : {};
    }

    async _callTerminal(endpoint, payload) {
        const host = this.pos.config.fiscal_service_ip?.trim();
        const port = this.pos.config.fiscal_service_port;
        const apiKey = this.pos.config.pos_fiscal_service_api_key?.trim();
        const merchantIdx = this.pos.config.bpos1_merchant_idx;

        if (!host || !port) {
            throw new Error(_t('Fiscal service IP/port is not configured on the POS settings.'));
        }
        if (!apiKey) {
            throw new Error(_t('Fiscal service API key is not configured on the POS settings.'));
        }

        const normalizedUrl = `http://${host}:${port}/${endpoint.replace(/^\/+/, '')}`;
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
        const terminalData = getTerminalData(response);
        const rrn = this._extractRrn(terminalData);
        if (rrn) {
            line.transaction_id = rrn;
            line.uiState = {
                ...line.uiState,
                bpos1_rrn: rrn,
            };
        }
        line.bpos1_terminal_id = terminalData?.terminal_id || '';
        line.bpos1_terminal_auth_code = terminalData?.auth_code || '';
        line.bpos1_terminal_pan = terminalData?.pan || '';
        const entryMode = terminalData?.entry_mode ?? terminalData?.EntryMode ?? '';
        line.bpos1_terminal_entry_mode = entryMode ? entryMode.toString() : '';
        const emvAid = terminalData?.emvAID ?? terminalData?.EMVAID ?? '';
        line.bpos1_terminal_emv_aid =
            ['2', '3'].includes(line.bpos1_terminal_entry_mode) ? emvAid : '';
        line.bpos1_terminal_payment_system = terminalData?.payment_system ?? terminalData?.paymentSystem ?? '';
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
