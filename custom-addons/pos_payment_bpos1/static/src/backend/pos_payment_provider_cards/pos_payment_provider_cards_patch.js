/** @odoo-module **/

import { PosPaymentProviderCards } from '@pos_payment_emulator/backend/pos_payment_provider_cards/pos_payment_provider_cards';

const EXTRA_PROVIDERS = [['bpos1', 'pos_payment_bpos1', 'BPOS1 Terminal']];

PosPaymentProviderCards.providers = PosPaymentProviderCards.providers || [];
for (const provider of EXTRA_PROVIDERS) {
    if (!PosPaymentProviderCards.providers.some((p) => p[0] === provider[0])) {
        PosPaymentProviderCards.providers.push(provider);
    }
}
