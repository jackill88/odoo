from odoo import http
from odoo.http import request

class PosFiscalController(http.Controller):

    @http.route('/pos_fiscal/get_order_fiscal_payload', type='jsonrpc', auth='user')
    def get_order_fiscal_payload(self, order_id):
        """
        Return fiscal JSON payload for a given POS order
        """
        order = request.env['pos.order'].browse(order_id)
        if not order.exists():
            return {"error": "Order not found"}
        return order.get_fiscal_payload()
    

    @http.route('/pos_fiscal/store_fiscal_id_in_order', type='jsonrpc', auth='user')
    def store_fiscal_id_in_order(self, order_id, document_fiscal_id):
        """
        Store fiscal ID in POS order
        """
        order = request.env['pos.order'].browse(order_id)
        if not order.exists():
            return {"error": "Order not found"}
        return order.save_unique_fiscal_id(document_fiscal_id, order)
    

    @http.route('/pos_fiscal/get_order_fiscal_id_for_refund', type='jsonrpc', auth='user')
    def get_order_fiscal_id(self, order_id):
        order = request.env['pos.order'].browse(order_id)
        if not order.exists():
            return {"error": "Order not found"}
        else:
            return order.get_original_fiscal_id()