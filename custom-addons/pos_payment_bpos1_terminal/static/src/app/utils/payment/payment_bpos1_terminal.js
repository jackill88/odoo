/** @odoo-module **/

import { PaymentInterface } from '@point_of_sale/app/utils/payment/payment_interface';
import { register_payment_method } from '@point_of_sale/app/services/pos_store';

class PaymentBpos1Terminal extends PaymentInterface {
    sendPaymentRequest(uuid) {
        const order = this.pos.getOrder();
        const line = order.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);
        if (!line) {
            return Promise.resolve(false);
        }
        line.setPaymentStatus('waitingCard');
        return new Promise((resolve) => {
            setTimeout(() => {
                line.setPaymentStatus('done');
                resolve(true);
            }, 800);
        });
    }

    sendPaymentCancel(order, uuid) {
        const line = order?.payment_ids.find((paymentLine) => paymentLine.uuid === uuid);
        if (line) {
            line.setPaymentStatus('cancel');
        }
        return Promise.resolve(true);
    }
}

register_payment_method('bpos1_terminal', PaymentBpos1Terminal);
