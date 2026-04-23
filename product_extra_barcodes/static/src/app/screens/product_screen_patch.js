/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";

patch(ProductScreen.prototype, {
    async _getProductByBarcode(code) {
        const product = await super._getProductByBarcode(...arguments);
        if (product) {
            return product;
        }
        return this._getProductByExtraBarcode(code?.base_code);
    },

    _getProductByExtraBarcode(codeValue) {
        if (!codeValue) {
            return undefined;
        }
        return this.pos.models["product.product"].find((item) =>
            item.hasExtraBarcode?.(codeValue)
        );
    },
});
