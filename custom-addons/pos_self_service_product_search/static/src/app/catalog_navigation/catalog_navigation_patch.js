/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SelfOrder } from "@pos_self_order/app/services/self_order_service";
import { LandingPage } from "@pos_self_order/app/pages/landing_page/landing_page";
import { OrderWidget } from "@pos_self_order/app/components/order_widget/order_widget";
import { onWillStart } from "@odoo/owl";

const originalSelfOrderSetup = SelfOrder.prototype.setup;
patch(SelfOrder.prototype, {
    async setup(...args) {
        this.catalogVisited = false;
        return originalSelfOrderSetup.apply(this, args);
    },
});

const originalLandingPageSetup = LandingPage.prototype.setup;
patch(LandingPage.prototype, {
    setup(...args) {
        originalLandingPageSetup.apply(this, args);
        onWillStart(() => {
            this.selfOrder.catalogVisited = false;
        });
    },
});

const originalOrderWidgetOnClick = OrderWidget.prototype.onClickleftButton;
patch(OrderWidget.prototype, {
    onClickleftButton() {
        const shouldGoBack = this.shouldGoBack();
        const currentPage = this.router.activeSlot;
        if (shouldGoBack && currentPage === "cart" && !this.selfOrder.catalogVisited) {
            this.selfOrder.catalogVisited = true;
            this.router.navigate("product_list");
            return;
        }
        return originalOrderWidgetOnClick.apply(this, arguments);
    },
});
