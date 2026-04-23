/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SelfOrder } from "@pos_self_order/app/services/self_order_service";

const originalSetup = SelfOrder.prototype.setup;

patch(SelfOrder.prototype, {
    async setup(...args) {
        const services = args[1] || {};
        const barcodeService = services.barcode;
        this._extraBarcodeHandler = (ev) => {
            if (this._handleExtraBarcodeEvent(ev.detail.barcode)) {
                ev.stopImmediatePropagation?.();
            }
        };
        if (barcodeService?.bus) {
            barcodeService.bus.addEventListener(
                "barcode_scanned",
                this._extraBarcodeHandler
            );
        }
        const result = await originalSetup.apply(this, args);
        return result;
    },

    _handleExtraBarcodeEvent(rawCode) {
        if (!this.ordering || !rawCode) {
            return false;
        }
        const product = this.models["product.product"].find((item) =>
            item.hasExtraBarcode?.(rawCode)
        );
        if (!product) {
            return false;
        }
        if (!product.self_order_available) {
            this.notification.add(_t("Product is not available"), {
                type: "danger",
            });
            return true;
        }
        const productTemplate = product.product_tmpl_id;
        if (productTemplate.isConfigurable()) {
            this.router.navigate("product", { id: productTemplate.id });
            return true;
        }
        this.addToCart(productTemplate, 1, "", {}, {});
        this.router.navigate("cart");
        return true;
    },
});
