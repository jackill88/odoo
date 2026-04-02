/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentPage } from "@pos_self_order/app/pages/payment_page/payment_page";
import { rpc } from "@web/core/network/rpc";
import { logPosMessage } from "@point_of_sale/app/utils/pretty_console_log";

const CONSOLE_COLOR = "#F5B427";
const HEALTH_TIMEOUT_MS = 5000;
const BPOS1_TIMEOUT_MS = 15000;
const RRN_KEYS = ['rrn', 'RRN', 'referenceNumber', 'reference_number', 'terminal_rrn'];

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

const extractBpos1Rrn = (response) => {
    if (!response) {
        return null;
    }
    for (const key of RRN_KEYS) {
        if (response[key]) {
            return response[key];
        }
    }
    return null;
};

const callBpos1Terminal = async (method, paymentMethod, order) => {
    const apiUrl = paymentMethod.bpos1_api_url?.trim();
    const apiKey = paymentMethod.bpos1_api_key?.trim();
    const merchantIdx = paymentMethod.bpos1_merchant_idx;

    if (!apiUrl) {
        throw new Error("BPOS1 API URL is missing on the payment method");
    }
    if (!apiKey) {
        throw new Error("BPOS1 API key is missing on the payment method");
    }

    const decimals = order.currency_id?.decimal_places ?? 2;
    const payload = buildBpos1Payload(order, decimals);
    if (merchantIdx != null) {
        payload.merchant_idx = merchantIdx;
    }

    const response = await fetchWithTimeout(
        formatBpos1Url(apiUrl, method),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": apiKey,
            },
            body: JSON.stringify(payload),
        },
        BPOS1_TIMEOUT_MS
    );

    const text = await response.text();
    if (!response.ok) {
        const detail = text || response.statusText;
        throw new Error(`BPOS1 terminal error: ${detail}`);
    }

    if (!text) {
        return null;
    }

    try {
        return JSON.parse(text);
    } catch (error) {
        return { result: text };
    }
};

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

        if (paymentMethod?.use_payment_terminal === "bpos1") {
            try {
                const endpoint = currentOrder.amount_total < 0 ? "/terminal-refund" : "/terminal-pay";
                const response = await callBpos1Terminal(endpoint, paymentMethod, currentOrder);
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
    },
});
