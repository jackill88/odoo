# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.fields import Domain


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    bpos1_terminal_merchant_id = fields.Char(string='Terminal Merchant ID')
    bpos1_terminal_device_id = fields.Char(string='Terminal Device ID')
    bpos1_terminal_store_code = fields.Char(string='Terminal Store Code')
    bpos1_terminal_token = fields.Char(string='Terminal Token')
    bpos1_terminal_secret = fields.Char(string='Terminal Secret')

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [
            ('bpos1_terminal', 'BPOS1 Terminal')
        ]

    @api.model
    def _load_pos_self_data_domain(self, data, config):
        domain = super()._load_pos_self_data_domain(data, config)
        if config.self_ordering_mode == 'kiosk':
            domain = Domain.OR([
                [('use_payment_terminal', '=', 'bpos1_terminal'), ('id', 'in', config.payment_method_ids.ids)],
                domain,
            ])
        return domain

    @api.model
    def _load_pos_data_fields(self, config):
        fields_list = super()._load_pos_data_fields(config)
        for field_name in (
            'bpos1_terminal_merchant_id',
            'bpos1_terminal_device_id',
            'bpos1_terminal_store_code',
            'bpos1_terminal_token',
            'bpos1_terminal_secret',
        ):
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list

    @api.model
    def _load_pos_self_data_fields(self, config):
        fields_list = super()._load_pos_self_data_fields(config)
        for field_name in (
            'bpos1_terminal_merchant_id',
            'bpos1_terminal_device_id',
            'bpos1_terminal_store_code',
            'bpos1_terminal_token',
            'bpos1_terminal_secret',
        ):
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list
    
    def _payment_request_from_kiosk(self, order):
        if self.use_payment_terminal != 'bpos1_terminal':
            return super()._payment_request_from_kiosk(order)

        order.add_payment({
            'amount': order.amount_total,
            'payment_date': fields.Datetime.now(),
            'payment_method_id': self.id,
            'pos_order_id': order.id,
        })
        order.action_pos_order_paid()
        order._send_payment_result('Success')
        return 'Success'
