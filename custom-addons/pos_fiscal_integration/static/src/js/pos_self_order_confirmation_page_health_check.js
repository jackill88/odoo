/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentPage } from "@pos_self_order/app/pages/payment_page/payment_page";
import { rpc } from "@web/core/network/rpc";
import { logPosMessage } from "@point_of_sale/app/utils/pretty_console_log";

const CONSOLE_COLOR = "#F5B427";
const HEALTH_TIMEOUT_MS = 5000;
const BPOS1_TIMEOUT_MS = 86400000;
const IN_PROGRESS_STATUSES = new Set(["pending", "processing", "created", "queued"]);
const FAILED_STATUSES = new Set([
    "failed",
    "declined",
    "cancelled",
    "canceled",
    "rejected",
    "error",
    "aborted",
    "timeout",
    "denied",
]);
const RRN_KEYS = ['rrn', 'RRN', 'referenceNumber', 'reference_number', 'terminal_rrn'];
const generateIdempotencyKey = () => {
    // const cryptoImpl = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined;
    // if (cryptoImpl && typeof cryptoImpl.randomUUID === 'function') {
    //     return cryptoImpl.randomUUID();
    // }
    // return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    return "1776019706890-xkdnf4b3xw";
};

const fetchWithTimeout = async (url, options, timeoutMs = HEALTH_TIMEOUT_MS) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(url, { ...options, signal: controller.signal });
        return response;
    } finally {
        clearTimeout(timeoutId);
    }
};

const formatBpos1Url = (baseUrl, endpoint) =>
    `${baseUrl.replace(/\/+$/, "")}/${endpoint.replace(/^\/+/, "")}`;

const buildBpos1Payload = (order, decimals) => {
    const amount = Math.round(Math.abs(order.amount_total)* Math.pow(10, decimals));
    const amountMinor = 0;
    return {
        amount: amount,
        amount_minor: amountMinor,
        currency_decimals: decimals,
    };
};

const normalizeBpos1Response = (response) => {
    const firstLevel = response?.result ?? response ?? {};
    return firstLevel?.result ?? firstLevel;
};

const extractBpos1Rrn = (response) => {
    const terminalData = normalizeBpos1Response(response);
    if (!terminalData) {
        return null;
    }
    for (const key of RRN_KEYS) {
        if (terminalData[key]) {
            return terminalData[key];
        }
    }
    return null;
};

const callBpos1Terminal = async (method, config, order) => {
    const host = config.fiscal_service_ip?.trim();
    const port = config.fiscal_service_port;
    const apiKey = config.pos_fiscal_service_api_key?.trim();
    const merchantIdx = 1;

    if (!host || !port) {
        throw new Error("Fiscal service IP/port is not configured on POS settings");
    }
    if (!apiKey) {
        throw new Error("Fiscal service API key is not configured on POS settings");
    }

    const decimals = order.currency_id?.decimal_places ?? 2;
    const payload = buildBpos1Payload(order, decimals);

    const baseUrl = `http://${host}:${port}`;
    const formattedUrl = formatBpos1Url(baseUrl, method);
    const baseHeaders = {
        "x-api-key": apiKey,
    };
    const idempotencyKey = generateIdempotencyKey();

    if (merchantIdx != null) {
        payload.merchant_idx = merchantIdx;
    }

    const response = await fetchWithTimeout(
        formattedUrl,
        {
            method: "POST",
            headers: {
                ...baseHeaders,
                "Content-Type": "application/json",
                "X-Idempotency-Key": idempotencyKey,
            },
            body: JSON.stringify(payload),
        },
        BPOS1_TIMEOUT_MS
    );

    let operation = await parseBpos1Response(response, "BPOS1 terminal error");

    const operationId = extractOperationId(operation);
    if (!operationId) {
        throw new Error("BPOS1 terminal error: Operation missing an ID");
    }

    const finalOperation = await waitForTerminalOperation(baseUrl, operationId, baseHeaders);
    ensureTerminalSuccess(finalOperation);
    return finalOperation;
};

const parseBpos1Response = async (response, prefix) => {
    const text = await response.text();
    if (!response.ok) {
        const detail = text || response.statusText;
        throw new Error(`${prefix}: ${detail}`);
    }

    if (!text) {
        return {};
    }

    try {
        return JSON.parse(text);
    } catch (error) {
        return { result: text };
    }
};

const getTerminalData = (response) => {
    const firstLevel = response?.result ?? response ?? {};
    const terminalData = firstLevel?.result ?? firstLevel ?? {};
    const aggregated = { ...terminalData };
    const rootId = response?.id ?? firstLevel?.id;
    if (rootId && !aggregated.id) {
        aggregated.id = rootId;
    }
    return aggregated;
};

const extractOperationId = (operation) => {
    const terminalData = getTerminalData(operation);
    return terminalData?.id ?? null;
};

const getNormalizedStatus = (operation) => {
    const terminalData = getTerminalData(operation);
    if (!terminalData?.status) {
        return "";
    }
    return terminalData.status.toString().trim().toLowerCase();
};

const getTerminalFailureMessage = (operation) => {
    const terminalData = getTerminalData(operation);
    return (
        terminalData?.message ||
        terminalData?.status_detail ||
        terminalData?.error ||
        terminalData?.reason ||
        terminalData?.status ||
        "Unknown terminal failure."
    );
};

const waitForTerminalOperation = async (baseUrl, operationId, headers) => {
    const pollUrl = formatBpos1Url(baseUrl, `terminal-operations/${operationId}`);
    const deadline = Date.now() + BPOS1_TIMEOUT_MS;

    while (Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, HEALTH_TIMEOUT_MS));
        const response = await fetchWithTimeout(
            pollUrl,
            {
                method: "GET",
                headers,
            },
            HEALTH_TIMEOUT_MS
        );
        const operation = await parseBpos1Response(response, "BPOS1 terminal status error");
        const status = getNormalizedStatus(operation);
        if (!isInProgressStatus(status)) {
            return operation;
        }
    }

    throw new Error("BPOS1 terminal error: Terminal operation timed out. Please try again.");
};

const isInProgressStatus = (status) => status && IN_PROGRESS_STATUSES.has(status);

const isFailedStatus = (status) => status && FAILED_STATUSES.has(status);

const ensureTerminalSuccess = (operation) => {
    const status = getNormalizedStatus(operation);
    if (isFailedStatus(status)) {
        throw new Error(`BPOS1 terminal error: ${getTerminalFailureMessage(operation)}`);
    }
};

// The self-order flow never cancels a terminal operation once sent, so
// /terminal-operations/{id}/cancel is intentionally unused here.

patch(PaymentPage.prototype, {
    async startPayment() {
        const { config, access_token, currentOrder } = this.selfOrder;

        if (config.use_pos_fiscal_service) {
            const host = config.fiscal_service_ip;
            const port = config.fiscal_service_port;
            const apiKey = config.pos_fiscal_service_api_key;

            const checkEndpoint = async (path) => {
                await fetchWithTimeout(`http://${host}:${port}${path}`, {
                    method: "GET",
                    headers: {
                        "x-api-key": apiKey,
                    },
                });
            };

            logPosMessage(
                "Store",
                "PaymentPage - startPayment() (patched)",
                "POS Fiscal integration: checking fiscal and terminal health",
                CONSOLE_COLOR
            );

            try {
                await checkEndpoint("/health");
                await checkEndpoint("/payment-terminal-health");
                await new Promise((resolve) => setTimeout(resolve, 800));
            } catch (error) {
                this.selfOrder.handleErrorNotification(error);
                this.selfOrder.paymentError = true;
                return;
            }
        }

        const paymentMethod = this.selectedPaymentMethod;
        let terminalRrn = null;

        if (paymentMethod?.use_payment_terminal === "bpos1_terminal") {
            try {
                const endpoint = currentOrder.amount_total < 0 ? "/terminal-refund" : "/terminal-pay";
                const response = await callBpos1Terminal(endpoint, config, currentOrder);
                terminalRrn = extractBpos1Rrn(response);
            } catch (error) {
                this.selfOrder.handleErrorNotification(error);
                this.selfOrder.paymentError = true;
                return;
            }
        }

        if (super.startPayment) {
            const payload = {
                order: currentOrder.serializeForORM(),
                access_token: access_token,
                payment_method_id: this.state.paymentMethodId,
            };
            if (terminalRrn) {
                payload.terminal_rrn = terminalRrn;
            }

            try {
                await rpc(`/kiosk/payment/${config.id}/kiosk`, payload);
            } catch (error) {
                this.selfOrder.handleErrorNotification(error);
                this.selfOrder.paymentError = true;
            }
        }

}
});
