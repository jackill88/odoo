/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentPage } from "@pos_self_order/app/pages/payment_page/payment_page";
import { logPosMessage } from "@point_of_sale/app/utils/pretty_console_log";

export const CONSOLE_COLOR = "#F5B427";

patch(PaymentPage.prototype, {
    async startPayment() {

        if (this.selfOrder.config.use_pos_fiscal_service) {
            const pos_fiscal_service_addess = this.selfOrder.config.fiscal_service_ip;
            const pos_fiscal_service_port = this.selfOrder.config.fiscal_service_port;
            const pos_fiscal_service_api_key = this.selfOrder.config.pos_fiscal_service_api_key;

            const controller = new AbortController();
            const timeoutMs = 5000; // 5 seconds timeout for health check
            const timeout = setTimeout(() => controller.abort(), timeoutMs);

            logPosMessage(
                "Store",
                "PaymentPage - startPayment() (patched)",
                "POS Fiscal integration: checking fiscal service health before payment",
                CONSOLE_COLOR
            );

            try {
                const healthResponse = await fetch(
                    `http://${pos_fiscal_service_addess}:${pos_fiscal_service_port}/health`,
                    {
                        method: "GET",
                        headers: {
                            "x-api-key": pos_fiscal_service_api_key,
                        },
                        signal: controller.signal,
                    }
                );

                clearTimeout(timeout);

                if (!healthResponse.ok) {
                    throw new Error(
                        `Fiscal service health error: ${healthResponse.status} ${healthResponse.statusText}`
                    );
                }
            } catch (error) {
                clearTimeout(timeout);

                if (error.name === "AbortError") {
                    console.error("Fiscal service health check timed out");
                } else {
                    console.error(
                        "POS Fiscal integration: fiscal service health check failed",
                        error
                    );
                }

                // Surface error to the self-order UI and stop payment flow
                this.selfOrder.handleErrorNotification(error);
                this.selfOrder.paymentError = true;
                return;
            }
        }

        // If fiscal service is healthy (or disabled), continue with the normal payment flow
        if (super.startPayment) {
            return super.startPayment();
        } else {
            // Fallback in case super.startPayment is not available for some reason
            return;
        }
    },
});

