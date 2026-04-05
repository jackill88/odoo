/** @odoo-module **/

import { registry } from "@web/core/registry";

export const WeightedGoodsBarcodeService = {
    dependencies: ["barcode_reader", "pos_store"],
    async start(env, deps) {
        const { barcode_reader, pos_store } = deps;
        if (!barcode_reader || !pos_store) {
            return;
        }
        const unregister = barcode_reader.register({
            weighted_goods: (parsed) => pos_store.handleWeightedGoodsBarcode(parsed),
        });
        return {
            stop() {
                unregister?.();
            },
        };
    },
};

registry.category("services").add("weighted_goods_barcode", WeightedGoodsBarcodeService);
