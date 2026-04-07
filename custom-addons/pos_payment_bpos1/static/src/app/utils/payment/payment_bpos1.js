/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { AlertDialog } from '@web/core/confirmation_dialog/confirmation_dialog';
import { PaymentInterface } from '@point_of_sale/app/utils/payment/payment_interface';
import { register_payment_method } from '@point_of_sale/app/services/pos_store';

const RRN_KEYS = ['rrn', 'RRN', 'referenceNumber', 'reference_number', 'terminal_rrn'];
const generateIdempotencyKey = () => {
    return "bd5683bc-1f4a-4bab-a2fe-e3a027bb1ed4";
    // const cryptoImpl = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined;
    // if (cryptoImpl && typeof cryptoImpl.randomUUID === 'function') {
    //     return cryptoImpl.randomUUID();
    // }
    // return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
};
const IN_PROGRESS_STATUSES = new Set(['pending', 'processing', 'created', 'queued']);
const FAILED_STATUSES = new Set([
    'failed',
    'declined',
    'cancelled',
    'canceled',
    'rejected',
    'error',
    'aborted',
    'timeout',
    'denied',
]);
const OPERATION_POLL_INTERVAL_MS = 1000;
const OPERATION_POLL_TIMEOUT_MS = 86400000;

function getTerminalData(response) {
    const firstLevel = response?.result ?? response ?? {};
    const terminalData = firstLevel?.result ?? firstLevel ?? {};
    const aggregated = { ...terminalData };
    const rootId = response?.id ?? firstLevel?.id;
    if (rootId && !aggregated.id) {
        aggregated.id = rootId;
    }
    return aggregated;
}

export class PaymentBpos1 extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this._pendingTerminalOperations = new Map();
    }

    async sendPaymentRequest(uuid) {
        const line = this.pos.getOrder().getPaymentlineByUuid(uuid);
        if (!line) {
            return false;
        }

        const isRefund = line.amount < 0;
        const payload = this._buildPayload(line, isRefund);
        line.setPaymentStatus('waitingCard');
        const idempotencyKey = generateIdempotencyKey();
        try {
            const endpoint = isRefund ? '/terminal-refund' : '/terminal-pay';
            if (!idempotencyKey) {
                throw new Error(_t('BPOS1 terminal error: Unable to generate a unique request identifier.'));
            }
            const response = await this._callTerminal(endpoint, payload, idempotencyKey, uuid);
            this._handleSuccess(line, response, idempotencyKey);
            return true;
        } catch (error) {
            this._handleError(line, error);
            return false;
        }
    }

    async sendPaymentCancel(order, uuid) {
        if (!uuid) {
            return true;
        }

        const pending = this._pendingTerminalOperations.get(uuid);
        if (!pending) {
            return true;
        }

        try {
            await this._cancelPendingOperation(pending);
            return true;
        } catch (error) {
            const detail = error?.message || _t('BPOS1 terminal cancellation failed.');
            this.env.services.dialog.add(AlertDialog, {
                title: _t('BPOS1 Error'),
                body: detail,
            });
            return false;
        }
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

    async _callTerminal(endpoint, payload, idempotencyKey, lineUuid) {
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

        const baseUrl = `http://${host}:${port}`;
        const normalizedUrl = `${baseUrl}/${endpoint.replace(/^\/+/, '')}`;
        const baseHeaders = {
            'x-api-key': apiKey,
        };
        const postHeaders = {
            ...baseHeaders,
            'Content-Type': 'application/json',
            'X-Idempotency-Key': idempotencyKey,
        };
        const body = {
            ...payload,
            ...(merchantIdx != null ? { merchant_idx: merchantIdx } : {}),
        };

        const response = await fetch(normalizedUrl, {
            method: 'POST',
            headers: postHeaders,
            body: JSON.stringify(body),
        });

        const operation = await this._parseResponse(response);
        const operationId = this._getOperationId(operation);
        const pendingKey = lineUuid ?? idempotencyKey;
        if (pendingKey && operationId) {
            this._pendingTerminalOperations.set(pendingKey, {
                operationId,
                baseUrl,
                headers: baseHeaders,
            });
        }

        try {
            const finalOperation = await this._waitForTerminalOperation(baseUrl, operation, baseHeaders);
            this._ensureTerminalSuccess(finalOperation);
            return finalOperation;
        } finally {
            if (pendingKey) {
                this._pendingTerminalOperations.delete(pendingKey);
            }
        }
    }

    async _waitForTerminalOperation(baseUrl, operation, pollHeaders) {
        const operationId = this._getOperationId(operation);
        if (!operationId) {
            throw new Error(
                _t('BPOS1 terminal error: Operation identifier is missing from the terminal response.')
            );
        }

        const status = this._getTerminalStatus(operation);
        if (!this._isTerminalPendingStatus(status)) {
            return operation;
        }

        const pollUrl = `${baseUrl}/terminal-operations/${operationId}`;
        const deadline = Date.now() + OPERATION_POLL_TIMEOUT_MS;
        while (Date.now() < deadline) {
            await this._sleep(OPERATION_POLL_INTERVAL_MS);
            const response = await fetch(pollUrl, {
                method: 'GET',
                headers: pollHeaders,
            });
            const nextOperation = await this._parseResponse(response, {
                errorMessagePrefix: _t('BPOS1 terminal status error'),
            });
            const nextStatus = this._getTerminalStatus(nextOperation);
            if (!this._isTerminalPendingStatus(nextStatus)) {
                return nextOperation;
            }
        }

        throw new Error(_t('BPOS1 terminal error: Terminal operation timed out. Please try again.'));
    }

    async _cancelPendingOperation(pending) {
        const cancelUrl = `${pending.baseUrl}/terminal-operations/${pending.operationId}/cancel`;
        const headers = {
            ...pending.headers,
            'Content-Type': 'application/json',
        };

        const response = await fetch(cancelUrl, {
            method: 'POST',
            headers,
        });

        await this._parseResponse(response, {
            errorMessagePrefix: _t('BPOS1 terminal cancellation error'),
        });
    }

    _ensureTerminalSuccess(operation) {
        const terminalData = getTerminalData(operation);
        const status = this._getTerminalStatus(operation);
        if (this._isTerminalFailedStatus(status)) {
            const detail = this._getTerminalFailureMessage(terminalData);
            throw new Error(_t('BPOS1 terminal error: %s', detail));
        }
    }

    _getOperationId(operation) {
        const terminalData = getTerminalData(operation);
        return terminalData?.id ?? null;
    }

    _getTerminalStatus(operation) {
        const terminalData = getTerminalData(operation);
        if (!terminalData?.status) {
            return '';
        }
        return terminalData.status.toString().trim().toLowerCase();
    }

    _isTerminalPendingStatus(status) {
        return status ? IN_PROGRESS_STATUSES.has(status) : false;
    }

    _isTerminalFailedStatus(status) {
        return status ? FAILED_STATUSES.has(status) : false;
    }

    _getTerminalFailureMessage(terminalData) {
        return (
            terminalData?.message ||
            terminalData?.status_detail ||
            terminalData?.error ||
            terminalData?.reason ||
            terminalData?.status ||
            _t('Unknown terminal failure.')
        );
    }

    async _parseResponse(response, { errorMessagePrefix } = {}) {
        const content = await response.text();
        const prefix = errorMessagePrefix ?? _t('BPOS1 terminal error');
        if (!response.ok) {
            const detail = content || response.statusText;
            throw new Error(_t('%s: %s', prefix, detail));
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

    _sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    _handleSuccess(line, response, idempotencyKey) {
        const terminalData = getTerminalData(response);
        const rrn = this._extractRrn(terminalData);
        if (rrn) {
            line.transaction_id = rrn;
        }
        const nextUiState = {
            ...(line.uiState ?? {}),
            ...(rrn ? { bpos1_rrn: rrn } : {}),
            ...(idempotencyKey ? { bpos1_idempotency_key: idempotencyKey } : {}),
        };
        line.uiState = nextUiState;
        if (idempotencyKey) {
            line.bpos1_terminal_idempotency_key = idempotencyKey;
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
