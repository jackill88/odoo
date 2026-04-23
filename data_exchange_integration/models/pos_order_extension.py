from odoo import models, fields, api
from datetime import datetime


class PosOrder(models.Model):
    _inherit = "pos.order"

    # extra fields

    data_exchange_processed = fields.Boolean(string='Processed by Data Exchange integration',
                                             index=True)

    data_exchange_external_id = fields.Char(
        string="Data Exchange: External ID",
        size=36,
        help="Data Exchange: External ID",
        index=True
    )

    _index = [
        ('pos_order_data_exchange_processed_false_idx', 'btree(data_exchange_processed) WHERE data_exchange_processed = FALSE'),
        ('pos_order_data_exchange_processed_true_idx', 'btree(data_exchange_processed) WHERE data_exchange_processed = TRUE'),
    ]


    def action_pos_order_data_exchange_mark_as_not_processed(self):
        order_ids = self.env.context.get('active_ids') or self.ids
        orders = self.browse(order_ids)
        if orders:
            orders.write({'data_exchange_processed': False})
        return True

    
