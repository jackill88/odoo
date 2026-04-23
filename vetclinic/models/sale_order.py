from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    animal_id = fields.Many2one(
        'animal',
        string='Animal',
        domain="[(\'customer_id\', '=', partner_id)]"
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_clear_animal(self):
        if self.animal_id and self.animal_id.customer_id != self.partner_id:
            self.animal_id = False
