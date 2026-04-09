/** @odoo-module **/

import { registry } from "@web/core/registry";

export const WeightedGoodsBarcodeService = {
    dependencies: ["barcode_reader", "pos"],
    async start(env, deps) {
        const { barcode_reader, pos } = deps;
        if (!barcode_reader || !pos) {
            return;
        }
        const unregister = barcode_reader.register({
            weighted_goods: (parsed) => pos.handleWeightedGoodsBarcode(parsed),
        });
        return {
            stop() {
                unregister?.();
            },
        };
    },
};

registry.category("services").add("weighted_goods_barcode", WeightedGoodsBarcodeService);
