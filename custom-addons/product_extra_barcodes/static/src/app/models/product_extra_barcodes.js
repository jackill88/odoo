/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductProduct } from "@point_of_sale/app/models/product_product";
import { ProductTemplate } from "@point_of_sale/app/models/product_template";
import {
    normalizedExtraBarcodeValues,
    parseExtraBarcodeValues,
} from "../utils/extra_barcode_utils";

patch(ProductProduct.prototype, {
    get extraBarcodes() {
        return parseExtraBarcodeValues(this.extra_barcode_values);
    },

    hasExtraBarcode(value) {
        if (!value) {
            return false;
        }
        return this.extraBarcodes.some((item) => item === value);
    },

    get normalizedExtraBarcodes() {
        return normalizedExtraBarcodeValues(this.extra_barcode_values);
    },

    get searchString() {
        const base = super.searchString;
        const extra = this.normalizedExtraBarcodes;
        return extra ? `${base} ${extra}` : base;
    },
});

patch(ProductTemplate.prototype, {
    get normalizedExtraBarcodes() {
        return normalizedExtraBarcodeValues(this.extra_barcode_values);
    },

    get searchString() {
        const base = super.searchString;
        const extra = this.normalizedExtraBarcodes;
        return extra ? `${base} ${extra}` : base;
    },
});
