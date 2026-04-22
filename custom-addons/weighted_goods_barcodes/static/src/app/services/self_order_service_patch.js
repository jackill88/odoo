/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SelfOrder } from "@pos_self_order/app/services/self_order_service";
import { tryParseWeightedBarcode } from "./weighted_goods_barcode_parser";

const originalSelfOrderSetup = SelfOrder.prototype.setup;
patch(SelfOrder.prototype, {
    async setup(...args) {
        const services = args[1] || {};
        const barcodeService = services.barcode;
        this._weightedGoodsBarcodeHandler = (ev) => {
            if (this._handleWeightedGoodsBarcodeEvent(ev.detail.barcode)) {
                ev.stopImmediatePropagation?.();
            }
        };
        if (barcodeService?.bus) {
            barcodeService.bus.addEventListener(
                "barcode_scanned",
                this._weightedGoodsBarcodeHandler
            );
        }
        const result = await originalSelfOrderSetup.apply(this, args);
        return result;
    },

    _handleWeightedGoodsBarcodeEvent(rawCode) {
        const prefix = this.config?.weighted_goods_barcode_prefix ?? null;
        const parsed = tryParseWeightedBarcode(rawCode, prefix);
        if (!parsed) {
            return false;
        }
        this.handleWeightedGoodsBarcode(parsed);
        return true;
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
            this.notification.add(_t("Product not found"), {
                type: "danger",
            });
            return;
        }
        if (!product.self_order_available) {
            this.notification.add(_t("Product is not available"), {
                type: "danger",
            });
            return;
        }
        const productTemplate = product.product_tmpl_id;
        if (productTemplate.isConfigurable()) {
            this.router.navigate("product", { id: productTemplate.id });
            return;
        }
        const quantity = decoded.weight / 1000;
        if (quantity <= 0) {
            return;
        }
        this.addToCart(productTemplate, quantity, "", {}, {});
        this.router.navigate("cart");
    },
});
