/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { BarcodeReader } from "@point_of_sale/app/services/barcode_reader_service";

const WEIGHTED_BARCODE_DIGITS = 13;
const WEIGHTED_PLU_LENGTH = 5;
const WEIGHTED_WEIGHT_LENGTH = 5;

patch(BarcodeReader.prototype, {
    setup() {
        super.setup();
        this.weightedGoodsBarcodePrefix = null;
    },

    async _scan(code) {
        if (!code) {
            return;
        }

        const weightedBarcode = this._tryParseWeightedBarcode(code);
        if (weightedBarcode) {
            const cbMaps = this.exclusiveCbMap ? [this.exclusiveCbMap] : [...this.cbMaps];
            await this._dispatchWeightedBarcode(cbMaps, weightedBarcode);
            return;
        }

        return super._scan(...arguments);
    },

    _tryParseWeightedBarcode(rawCode) {
        const prefix = this.weightedGoodsBarcodePrefix;
        if (prefix === null || prefix === undefined) {
            return null;
        }

        const digits = (rawCode || "").replace(/[^0-9]/g, "");
        if (digits.length !== WEIGHTED_BARCODE_DIGITS) {
            return null;
        }

        const prefixDigits = String(prefix).padStart(2, "0");
        if (!digits.startsWith(prefixDigits)) {
            return null;
        }

        const start = prefixDigits.length;
        const pluPart = digits.slice(start, start + WEIGHTED_PLU_LENGTH);
        const weightPart = digits.slice(start + WEIGHTED_PLU_LENGTH, start + WEIGHTED_PLU_LENGTH + WEIGHTED_WEIGHT_LENGTH);
        if (pluPart.length < WEIGHTED_PLU_LENGTH || weightPart.length < WEIGHTED_WEIGHT_LENGTH) {
            return null;
        }

        const plu = parseInt(pluPart, 10);
        const weight = parseInt(weightPart, 10);
        if (Number.isNaN(plu) || Number.isNaN(weight)) {
            return null;
        }

        return {
            type: "weighted_goods",
            code: rawCode,
            base_code: `${prefixDigits}${pluPart}${"0".repeat(WEIGHTED_WEIGHT_LENGTH)}`,
            plu,
            weight,
            value: weight,
        };
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
