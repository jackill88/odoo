from odoo import models, fields, api


class PricelistPriceUpdateWizard(models.TransientModel):
    _name = 'pricelist.price.update.wizard'
    _description = 'Update Pricelist Prices'

    pricelist_id = fields.Many2one('product.pricelist', required=True)
    order_id = fields.Many2one('purchase.order', required=True)

    line_ids = fields.One2many(
        'pricelist.price.update.wizard.line',
        'wizard_id'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        order = self.env['purchase.order'].browse(self.env.context.get('active_id'))
        res['order_id'] = order.id

        lines = []
        for line in order.order_line:
            if not line.product_id:
                continue

            # Create line record immediately - ok for transient models
            line_rec = self.env['pricelist.price.update.wizard.line'].create({
                'wizard_id': self.id,
                'product_id': line.product_id.id,
                'cost': line.price_unit,
            })
            lines.append(line_rec.id)

        res['line_ids'] = [(6, 0, lines)]  # link the real lines to the wizard
        return res
        

    def action_save_all(self):
        for line in self.line_ids:
            line._save_price()


class PricelistPriceUpdateWizardLine(models.TransientModel):
    _name = 'pricelist.price.update.wizard.line'
    _description = 'Wizard Line'

    wizard_id = fields.Many2one('pricelist.price.update.wizard')

    product_id = fields.Many2one('product.product', required=True)
    cost = fields.Float()
    current_price = fields.Float(compute='_compute_current_price', store=True)
    markup_percent = fields.Float(default=0.0, store=True)
    new_price = fields.Float(store=True, compute="_compute_new_price", inverse="_inverse_new_price")

    @api.depends('product_id', 'wizard_id.pricelist_id')
    def _compute_current_price(self):
        for line in self:
            pricelist = line.wizard_id.pricelist_id
            if not pricelist or not line.product_id:
                line.current_price = 0.0
                continue

            line.current_price = pricelist._get_product_price(
                line.product_id,
                1.0
            )

    @api.depends('cost', 'markup_percent')
    def _compute_new_price(self):
        """Compute the new price based on cost + markup"""
        for line in self:
            if line.cost is not None and line.markup_percent is not None:
                line.new_price = line.cost * (1 + line.markup_percent / 100)
            else:
                line.new_price = 0.0

    def _inverse_new_price(self):
        """If the user manually edits 'new_price', recalculate the markup_percent to match."""
        for line in self:
            if line.cost:
                line.markup_percent = (line.new_price / line.cost - 1) * 100
            else:
                line.markup_percent = 0.0

    @api.onchange('markup_percent', 'cost')
    def _onchange_markup(self):
        if self.cost:
            self.new_price = self.cost * (1 + self.markup_percent / 100)


    # main method that stores the price
    def _save_price(self):
        self.ensure_one()

        pricelist = self.wizard_id.pricelist_id
        product = self.product_id
        tmpl_id = product.product_tmpl_id.id

        # Search for an existing item that matches either product or template
        item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('applied_on', '=', '1_product'),
            '|',
            ('product_id', '=', product.id),
            ('product_tmpl_id', '=', tmpl_id),
        ], limit=1)

        vals = {
            'pricelist_id': pricelist.id,
            'product_id': product.id,
            'product_tmpl_id': tmpl_id,
            'applied_on': '1_product',
            'adjusted_manual_price': self.new_price,
        }

        if item:
            item.write(vals)
        else:
            self.env['product.pricelist.item'].create(vals)


    def action_save_price(self):
        self.ensure_one()
        self._save_price()

        # open this same wizard
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'pricelist.price.update.wizard', # The parent wizard model
                'res_id': self.wizard_id.id,                  # ID of the open wizard
                'view_mode': 'form',
                'target': 'new',                              # 'new' keeps it in a popup dialog
            }


# add new actions into Purchase order
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_open_price_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Pricelist',
            'res_model': 'pricelist.price.update.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
            }
        }

