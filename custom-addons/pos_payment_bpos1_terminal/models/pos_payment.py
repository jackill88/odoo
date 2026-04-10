# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    bpos1_terminal_id = fields.Char(string='BPOS1 Terminal ID')
    bpos1_terminal_auth_code = fields.Char(string='BPOS1 Approval Code')
    bpos1_terminal_pan = fields.Char(string='BPOS1 PAN')
    bpos1_terminal_entry_mode = fields.Char(string='BPOS1 Entry Mode')
    bpos1_terminal_emv_aid = fields.Char(string='BPOS1 EMV AID')
    bpos1_terminal_payment_system = fields.Char(string='BPOS1 payment system')
