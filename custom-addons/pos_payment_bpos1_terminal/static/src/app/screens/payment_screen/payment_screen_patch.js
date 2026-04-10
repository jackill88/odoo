/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { PaymentScreen } from '@point_of_sale/app/screens/payment_screen/payment_screen';
import { PaymentScreenBpos1TerminalPanel } from '../../components/bpos1_terminal_panel/bpos1_terminal_panel';

patch(PaymentScreen, {
    components: {
        ...PaymentScreen.components,
        PaymentScreenBpos1TerminalPanel,
    },
});
