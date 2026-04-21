from odoo import http
from odoo.http import request


class PosOrderExportController(http.Controller):
    @http.route(
        '/api/data-exchange/get-data/pos/by-internal-id/<int:pos_config_id>/pos-order/list',
        type='jsonrpc',
        auth='bearer',
        methods=['GET'],
        csrf=False,
    )
    def list_paid_orders_by_inernal_pos_config_id(self, pos_config_id, **params):
        """Return the paid POS orders and confirmed refunds for a single config."""
        config = request.env['pos.config'].sudo().browse(pos_config_id)
        if not config.exists():
            return {
                'error': f'Point of Sale configuration {pos_config_id} not found',
            }

        domain = [
            ('config_id', '=', config.id),
            ('state', 'in', ['paid', 'done']),
        ]
        orders = request.env['pos.order'].sudo().search(domain, order='date_order desc')

        return {
            'pos_config_id': config.id,
            'pos_order_ids': orders.ids,
            'order_count': len(orders),
        }
    

    @http.route(
        '/api/data-exchange/get-data/pos/by-external-id/<string:ext_pos_config_id>/pos-order/list',
        type='jsonrpc',
        auth='bearer',
        methods=['GET'],
        csrf=False,
    )
    def list_paid_orders_by_external_pos_config_id(self, ext_pos_config_id, **params):
        """Return the paid POS orders and confirmed refunds for a single config."""
        internal_pos_config = request.env['external.id.map'].search([
            ('external_id', '=', str(ext_pos_config_id)),
            ('model', '=', 'pos.config')
        ], limit=1)

        internal_pos_config_id = internal_pos_config.res_id

        if not internal_pos_config_id:
            return {
                'error': f'No matches found for external POS config ID {ext_pos_config_id}',
            }
        
        config = request.env['pos.config'].sudo().browse(internal_pos_config_id)
        if not config.exists():
            return {
                'error': f'Point of Sale configuration {internal_pos_config_id} not found',
            }

        domain = [
            ('config_id', '=', config.id),
            ('state', 'in', ['paid', 'done']),
        ]
        orders = request.env['pos.order'].sudo().search(domain, order='date_order desc')

        return {
            'pos_config_id': config.id,
            'pos_order_ids': orders.ids,
            'order_count': len(orders),
        }

    @http.route(
        '/api/data-exchange/get-data/pos/order/<int:order_id>',
        type='json',
        auth='bearer',
        methods=['GET'],
        csrf=False,
    )
    def get_order_by_id(self, order_id, **params):
        """Return a POS order with its lines plus external IDs for POS config and products."""
        order = request.env['pos.order'].sudo().browse(order_id)
        if not order.exists():
            return {'error': f'POS order {order_id} not found'}

        config = order.config_id
        config_external_id = self._get_external_id('pos.config', config.id) if config else None

        lines = []
        for line in order.lines:
            product = line.product_id
            product_external_id = self._get_external_id('product.template', product.product_tmpl_id) if product else None
            lines.append({
                'id': line.id,
                'name': line.name,
                'quantity': line.qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'price_subtotal': line.price_subtotal,
                'price_subtotal_incl': line.price_subtotal_incl,
                'product_id': product.id if product else None,
                'product_external_id': product_external_id,
                'tax_names': line.tax_ids.mapped('name'),
            })

        refunded_order = order.refunded_order_id or False
        return {
            'pos_order_id': order.id,
            'pos_config': {
                'id': config.id if config else None,
                'external_id': config_external_id,
            },
            'line_count': len(lines),
            'refunded_order_id': refunded_order.id if refunded_order else None,
            'refunded_order_external_id': self._get_external_id('pos.order', refunded_order.id) if refunded_order else None,
            'name': order.name,
            'state': order.state,
            'date_order': order.date_order,
            'amount_total': order.amount_total,
            'amount_paid': order.amount_paid,
            'lines': lines,
        }

    def _get_external_id(self, model_name, res_id):
        if not res_id:
            return None

        mapping = request.env['external.id.map'].sudo().search([
            ('model', '=', model_name),
            ('res_id', '=', res_id),
        ], limit=1)
        return mapping.external_id if mapping else None
