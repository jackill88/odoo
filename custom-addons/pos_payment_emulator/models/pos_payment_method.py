from odoo import api, fields, models
from odoo.fields import Domain


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        """Add the emulator to the available payment terminals."""
        selection = super()._get_payment_terminal_selection()
        return selection + [('emulator', 'Terminal Emulator')]

    emulator_mode = fields.Selection(
        selection=[
            ('always_success', 'Always succeed'),
            ('always_fail', 'Always fail'),
        ],
        string="Emulator mode",
        default='always_success',
        help="Controls how the POS payment emulator behaves.",
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Make emulator configuration available in the POS frontend."""
        fields_list = super()._load_pos_data_fields(config)
        fields_list += ['emulator_mode']
        return fields_list

    def _payment_request_from_kiosk(self, order):
        """Handle kiosk payment requests using the emulator terminal.

        For emulator payments, we immediately mark the order as paid and notify
        the self-order kiosk frontend via the existing bus mechanism.
        """
        if self.use_payment_terminal != 'emulator':
            return super()._payment_request_from_kiosk(order)

        self.ensure_one()
        order.add_payment({
            'amount': order.amount_total,
            'payment_date': fields.Datetime.now(),
            'payment_method_id': self.id,
            'pos_order_id': order.id,
        })
        order.action_pos_order_paid()
        order._send_payment_result("Success")
        return "Success"

    @api.model
    def _load_pos_self_data_domain(self, data, config):
        """Expose emulator payment methods to the self-order (kiosk) frontend."""
        domain = super()._load_pos_self_data_domain(data, config)
        if config.self_ordering_mode == 'kiosk':
            domain = Domain.OR([
                [('use_payment_terminal', '=', 'emulator'), ('id', 'in', config.payment_method_ids.ids)],
                domain,
            ])
        return domain

