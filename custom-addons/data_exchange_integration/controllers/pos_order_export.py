from odoo import fields, http
from odoo.http import request


class PosOrderExportController(http.Controller):
    @http.route(
        '/api/data-exchange/pos/by-internal-id/<int:pos_config_id>/pos-order/list',
        type='jsonrpc',
        auth='bearer',
        methods=['GET','POST'],
        csrf=False,
    )
    def list_paid_orders_by_inernal_pos_config_id(self, pos_config_id, **params):
        """Return unprocessed paid POS orders (with counts) for a single config."""
        config = request.env['pos.config'].sudo().browse(pos_config_id)
        if not config.exists():
            return {
                'error': f'Point of Sale configuration {pos_config_id} not found',
            }
        orders, sales_orders, refund_orders = self._fetch_paid_orders_with_split(
            config,
            extra_domain=[
                ('data_exchange_processed', '!=', True),
            ],
        )

        return {
            'pos_config_id': config.id,
            'pos_order_ids': orders.ids,
            'total_order_count': len(orders),
            'sale_order_count': len(sales_orders),
            'refund_order_count': len(refund_orders),
        }
    

    @http.route(
        '/api/data-exchange/pos/by-external-id/<string:ext_pos_config_id>/pos-order/list',
        type='jsonrpc',
        auth='bearer',
        methods=['GET','POST'],
        csrf=False,
    )
    def list_paid_orders_by_external_pos_config_id(self, ext_pos_config_id, **params):
        """Return paid POS sales and refunds (with counts) for a single config mapped by external ID."""
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

        orders, sales_orders, refund_orders = self._fetch_paid_orders_with_split(
            config,
            extra_domain=[
                ('data_exchange_processed', '!=', True),
            ],
        )

        return {
            'pos_config_id': config.id,
            'pos_order_ids': sales_orders.ids,
            'pos_refund_order_ids': refund_orders.ids,
            'total_order_count': len(orders),
            'sale_order_count': len(sales_orders),
            'refund_order_count': len(refund_orders),
        }

    def _fetch_paid_orders_with_split(self, config, extra_domain=None):
        """Return paid orders plus split sales/refunds for a config."""
        domain = [
            ('config_id', '=', config.id),
            ('state', 'in', ['paid', 'done']),
        ]
        if extra_domain:
            domain += extra_domain
        orders = request.env['pos.order'].sudo().search(domain, order='create_date asc')
        sales_orders = orders.filtered(lambda order: not order.is_refund)
        refund_orders = orders.filtered(lambda order: order.is_refund)
        return orders, sales_orders, refund_orders

    @http.route(
        '/api/data-exchange/pos/order/<int:order_id>',
        type='jsonrpc',
        auth='bearer',
        methods=['GET','POST'],
        csrf=False,
    )
    def get_order_by_id(self, order_id, **params):
        """Return a POS order with its lines plus external IDs for POS config and products."""
        order = request.env['pos.order'].sudo().browse(order_id)
        if not order.exists():
            return {'error': f'POS order {order_id} not found'}

        config = order.config_id
        config_external_id = self._get_external_id('pos.config', config.id) if config else None
        pricelist = order.pricelist_id
        pricelist_external_id = self._get_external_id('product.pricelist', pricelist.id) if pricelist else None

        client_timezone = (
            params.get('timezone')
            or request.httprequest.headers.get('X-Client-Timezone')
            or request.env.user.tz
            or 'UTC'
        )
        server_timezone = request.env.user.tz or 'UTC'
        if client_timezone == server_timezone:
            localized_date_order = (
                fields.Datetime.to_string(order.date_order)
                if order.date_order
                else None
            )
        else:
            localized_date_order = fields.Datetime.context_timestamp(
                order.with_context(tz=client_timezone), order.date_order
            )
            localized_date_order = (
                fields.Datetime.to_string(localized_date_order)
                if localized_date_order
                else None
            )

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
        payment_lines = []
        for payment in order.payment_ids:
            payment_method = payment.payment_method_id
            journal = payment_method.journal_id if payment_method else payment.journal_id
            is_cash = journal.type == 'cash' if journal else False
            payment_lines.append({
                'amount': payment.amount,
                'is_cash': is_cash,
            })
        return {
            'pos_order_id': order.id,
            'pos_config': {
                'id': config.id if config else None,
                'external_id': config_external_id,
            },
            'pricelist': {
                'id': pricelist.id if pricelist else None,
                'external_id': pricelist_external_id,
            },
            'line_count': len(lines),
            'refunded_order_id': refunded_order.id if refunded_order else None,
            'refunded_order_external_id': self._get_external_id('pos.order', refunded_order.id) if refunded_order else None,
            'name': order.name,
            'state': order.state,
            'date_order': localized_date_order,
            'amount_total': order.amount_total,
            'amount_paid': order.amount_paid,
            'lines': lines,
            'payment_lines': payment_lines,
        }

    @http.route(
        '/api/data-exchange/pos/order/<int:order_id>/mark-processed',
        type='jsonrpc',
        auth='bearer',
        methods=['POST'],
        csrf=False,
    )
    def mark_order_as_processed(self, order_id, **params):
        """Mark a pos.order as processed by the data exchange integration."""
        order = request.env['pos.order'].sudo().browse(order_id)
        if not order.exists():
            return {'error': f'POS order {order_id} not found'}

        payload = request.get_json_data()
        if payload:
            external_id = payload.get('order_external_id')
            if not external_id:
                return {'error': 'order_external_id is required in the payload'}
        else:
            return {'error': 'order_external_id is required in the payload'}
            

        order.write({
            'data_exchange_processed': True,
            'data_exchange_external_id': external_id,
        })
        return {
            'pos_order_id': order.id,
            'data_exchange_processed': order.data_exchange_processed,
            'data_exchange_external_id': order.data_exchange_external_id,
        }

    def _get_external_id(self, model_name, res_id):
        if not res_id:
            return None

        mapping = request.env['external.id.map'].sudo().search([
            ('model', '=', model_name),
            ('res_id', '=', res_id),
        ], limit=1)
        return mapping.external_id if mapping else None
