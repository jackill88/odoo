/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";

export class PaymentEmulator extends PaymentInterface {
    sendPaymentRequest(uuid) {
        super.sendPaymentRequest(uuid);

        const order = this.pos.getOrder();
        const line = order.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);
        if (!line) {
            return Promise.resolve(false);
        }

        // Show as "waiting for card" for a short time.
        line.setPaymentStatus("waitingCard");

        const mode = this.payment_method_id.emulator_mode || "always_success";
        const delay = 1200;

        return new Promise((resolve) => {
            setTimeout(() => {
                const success = mode === "always_success";
                if (success) {
                    line.setPaymentStatus("done");
                } else {
                    line.setPaymentStatus("retry");
                    this._showError(_t("Emulated payment failure."));
                }
                resolve(success);
            }, delay);
        });
    }

    sendPaymentCancel(order, uuid) {
        super.sendPaymentCancel(order, uuid);

        const line = order.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);
        if (line) {
            line.setPaymentStatus("cancel");
        }
        return Promise.resolve(true);
    }

    _showError(message, title = _t("Payment Emulator")) {
        this.env.services.dialog.add(AlertDialog, {
            title,
            body: message,
        });
    }
}

register_payment_method("emulator", PaymentEmulator);

