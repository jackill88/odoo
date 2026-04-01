import { formatProductName } from "@pos_self_order/app/utils";
import { ProductListPage } from "@pos_self_order/app/pages/product_list_page/product_list_page";
import { patch } from "@web/core/utils/patch";

const originalSetup = ProductListPage.prototype.setup;
const originalGetProducts = ProductListPage.prototype.getProducts;
const productCategoriesDescriptor = Object.getOwnPropertyDescriptor(
    ProductListPage.prototype,
    "productCategories"
);

patch(ProductListPage.prototype, {
    setup() {
        originalSetup.call(this);
        this.selfOrder.catalogVisited = true;
        this.state.searchQuery = this.state.searchQuery || "";
    },

    getProducts(category) {
        const products = originalGetProducts.call(this, category);
        return this.filterProducts(products);
    },

    filterProducts(products) {
        const query = (this.state.searchQuery || "").trim().toLowerCase();
        if (!query) {
            return products;
        }
        return products.filter((product) => this.productMatchesQuery(product, query));
    },

    productMatchesQuery(product, query) {
        const haystack = [
            formatProductName(product),
            product.name,
            product.default_code,
            product.barcode,
            product.full_product_name,
            product.product_tmpl_id?.display_name,
        ];
        return haystack.some((value) =>
            value?.toString?.().toLowerCase().includes(query)
        );
    },

    get productCategories() {
        const categories =
            productCategoriesDescriptor?.get?.call(this) ?? [];
        if (!this.searchActive) {
            return categories;
        }
        return categories.filter((category) => this.getProducts(category).length > 0);
    },

    get searchActive() {
        return Boolean((this.state.searchQuery || "").trim());
    },

    get noProductFound() {
        return this.searchActive && this.productCategories.length === 0;
    },
});
