# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from urllib.parse import urljoin

import requests
from odoo import fields, models, _
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

BPOS1_TIMEOUT = 15


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    bpos1_api_url = fields.Char(
        string='BPOS1 API Base URL',
        help='Base URL of the fiscal layer instance that exposes the /terminal-pay and /terminal-refund endpoints.',
    )
    bpos1_api_key = fields.Char(
        string='BPOS1 API Key',
        help='Security key that is passed as the x-api-key header when talking to the fiscal layer.',
    )
    bpos1_merchant_idx = fields.Integer(
        string='BPOS1 Merchant Index',
        help='Optional merchant index that is forwarded to the terminal (merchant_idx).',
    )

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('bpos1', 'BPOS1 Terminal')]

    def _load_pos_data_fields(self, config):
        fields_list = super()._load_pos_data_fields(config)
        fields_list += ['bpos1_api_url', 'bpos1_api_key', 'bpos1_merchant_idx']
        return fields_list

    def bpos1_send_payment_request(self, payload):
        self.ensure_one()
        self._ensure_pos_user()
        body = self._build_bpos1_payload(payload)
        return self._call_bpos1_api('/terminal-pay', body)

    def bpos1_send_refund_request(self, payload):
        self.ensure_one()
        self._ensure_pos_user()
        rrn = payload.get('original_rrn') or payload.get('rrn') or payload.get('refund_rrn')
        if not rrn:
            raise UserError(_('Refunds require an original transaction identifier (rrn).'))
        body = self._build_bpos1_payload(payload, rrn=rrn)
        return self._call_bpos1_api('/terminal-refund', body)

    def _ensure_pos_user(self):
        if not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessError(_('Only POS users are allowed to call the BPOS1 endpoints.'))

    def _build_bpos1_payload(self, payload, **extra):
        amount = self._bpos1_amount(payload)
        data = {'amount': amount}
        if payload.get('add_amount') is not None:
            data['add_amount'] = int(payload['add_amount'])
        if self.bpos1_merchant_idx:
            data['merchant_idx'] = self.bpos1_merchant_idx
        data.update(extra)
        return data

    def _bpos1_amount(self, payload):
        try:
            if payload.get('amount_minor') is not None:
                return int(payload['amount_minor'])
            amount = float(payload['amount'])
        except (TypeError, ValueError):
            raise UserError(_('A numeric amount is required to talk to the BPOS1 terminal.'))

        decimals = payload.get('currency_decimals')
        if decimals is None:
            decimals = self.env.company.currency_id.decimal_places
        try:
            decimals = int(decimals)
        except (TypeError, ValueError):
            raise UserError(_('Invalid currency decimals sent to the BPOS1 terminal.'))

        multiplier = 10 ** decimals
        return int(round(abs(amount) * multiplier))

    def _call_bpos1_api(self, endpoint, data):
        url = self.bpos1_api_url
        if not url:
            raise UserError(_('The POS payment method is missing the BPOS1 API URL.'))
        headers = self._bpos1_headers()
        request_url = urljoin(url.rstrip('/') + '/', endpoint.lstrip('/'))
        try:
            response = requests.post(request_url, json=data, headers=headers, timeout=BPOS1_TIMEOUT)
        except requests.exceptions.RequestException as exc:
            _logger.exception('BPOS1 terminal request failed')
            raise UserError(_('Unable to reach the BPOS1 terminal: %s') % exc)

        if response.status_code != 200:
            message = response.text or response.reason or response.status_code
            raise UserError(_('BPOS1 terminal returned an error: %s') % message)

        if not response.text:
            return {}
        try:
            return response.json()
        except ValueError:
            return {'result': response.text}

    def _bpos1_headers(self):
        if not self.bpos1_api_key:
            raise UserError(_('The BPOS1 API key is required to authenticate with the terminal.'))
        return {
            'x-api-key': self.bpos1_api_key,
            'Content-Type': 'application/json',
        }
