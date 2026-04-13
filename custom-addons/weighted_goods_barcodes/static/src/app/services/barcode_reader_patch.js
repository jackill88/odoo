/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { BarcodeReader } from "@point_of_sale/app/services/barcode_reader_service";
import { tryParseWeightedBarcode } from "./weighted_goods_barcode_parser";

patch(BarcodeReader.prototype, {
    setup() {
        super.setup();
        this.weightedGoodsBarcodePrefix = null;
    },

    async _scan(code) {
        if (!code) {
            return;
        }

        const weightedBarcode = tryParseWeightedBarcode(code, this.weightedGoodsBarcodePrefix);
        if (weightedBarcode) {
            const cbMaps = this.exclusiveCbMap ? [this.exclusiveCbMap] : [...this.cbMaps];
            await this._dispatchWeightedBarcode(cbMaps, weightedBarcode);
            return;
        }

        return super._scan(...arguments);
    },

    async _dispatchWeightedBarcode(cbMaps, parsed) {
        const callbacks = cbMaps.map((cbMap) => cbMap[parsed.type]).filter(Boolean);
        if (!callbacks.length) {
            this.showNotFoundNotification(parsed);
            return;
        }
        for (const cb of callbacks) {
            await cb(parsed);
        }
    },
});
