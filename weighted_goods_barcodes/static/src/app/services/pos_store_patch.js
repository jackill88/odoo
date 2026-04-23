/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    async processServerData() {
        const result = await super.processServerData(...arguments);
        this._syncWeightedGoodsBarcodePrefix();
        return result;
    },

    _syncWeightedGoodsBarcodePrefix() {
        if (this.barcodeReader) {
            this.barcodeReader.weightedGoodsBarcodePrefix = this.config?.weighted_goods_barcode_prefix ?? null;
        }
    },

    async handleWeightedGoodsBarcode(decoded) {
        if (!decoded) {
            return;
        }
        const product = this.models["product.product"].find((item) => {
            return (
                item.is_weighted_bc &&
                item.weighted_bc_plu_for_pos === decoded.plu
            );
        });
        if (!product) {
            this.barcodeReader?.showNotFoundNotification(decoded);
            return;
        }
        const quantity = decoded.weight / 1000;
        const values = {
            product_id: product,
            product_tmpl_id: product.product_tmpl_id,
        };
        if (quantity > 0) {
            values.qty = quantity;
        }
        await this.addLineToCurrentOrder(values, { code: decoded }, product.needToConfigure());
        this.numberBuffer.reset();
         this.showOptionalProductPopupIfNeeded(product);
    },

    showOptionalProductPopupIfNeeded(product) {
        if (product.pos_optional_product_ids?.length) {
            this.dialog.add(OptionalProductPopup, {
                productTemplate: product,
            });
        }
    }
});
