# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    adjusted_manual_price = fields.Float(string="Manual Price", min_display_digits='Manual Product Price')
    # add new option - last purchase price
    base = fields.Selection(
        selection_add=[('latest_purchase', 'Latest Purchase')],
        ondelete={'latest_purchase': 'cascade'}
    )

    def _get_price_label_base_str(self):
        self.ensure_one()
        if self.base == 'latest_purchase':
            return "latest purchase price"
        return super()._get_price_label_base_str()

    # extends the base class to be able to compute the base price for 'latest_purchase' option
    def _compute_base_price(self, product, quantity, uom, date, currency, **kwargs):
        if not self:
            return super()._compute_base_price(product, quantity, uom, date, currency, **kwargs)

        self.ensure_one()
        currency.ensure_one()

        # Handle our new base
        if self.base == 'latest_purchase':

           
            # use adjusted_manual_price if it's set
            if self.adjusted_manual_price > 0:

                price = self.adjusted_manual_price

                # use whatever selected is in this order
                src_currency = currency
                src_uom = uom

            else:

                PurchaseLine = self.env['purchase.order.line']

                domain = [
                    ('product_id', '=', product.id),
                    ('order_id.state', 'in', ['purchase', 'done']),
                    ('company_id', '=', self.env.company.id),
                ]

                if date:
                    domain.append(('date_order', '<=', date))

                pol = PurchaseLine.search(
                    domain,
                    order='date_order desc, id desc',
                    limit=1
                )

                if not pol:
                    # fallback if no purchase history
                    return super()._compute_base_price(product, quantity, uom, date, currency, **kwargs)

                src_currency = pol.order_id.currency_id
                src_uom = pol.product_uom_id

                # choose effective price (discount included)
                price = pol.price_unit_discounted or pol.price_unit

            # convert UoM
            if src_uom != uom:
                price = src_uom._compute_price(price, uom)

            # convert currency
            if src_currency != currency:
                price = src_currency._convert(
                    price,
                    currency,
                    self.env.company,
                    date,
                    round=False,
                )

            return price

        # all other bases use standard logic
        return super()._compute_base_price(product, quantity, uom, date, currency, **kwargs)


    # extends base class so the 'adjusted_manual_price' is used the same way as 'fixed_price' in some cases
    def _compute_price(self, product, quantity, uom, date, currency=None, **kwargs):
        self and self.ensure_one()  # self is at most one record
        product.ensure_one()
        uom.ensure_one()

        if self.base == 'latest_purchase' and self.adjusted_manual_price > 0:
            return self.adjusted_manual_price

        return super()._compute_price(product, quantity, uom, date, currency=None, **kwargs)