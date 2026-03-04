from odoo import models, fields, api
from datetime import datetime


class PosOrder(models.Model):
    _inherit = "pos.order"

    # extra fields
    document_fiscal_id = fields.Char(
        string="Unique fiscal ID",
        size=36,
        help="Unique fiscal ID (used for returns)."
    ) 

    def get_fiscal_order_lines(self):
        self.ensure_one()

        receipt_list = []

        for line in self.lines:
            product = line.product_id
            taxes = line.tax_ids_after_fiscal_position

            vat_rate = 0
            if taxes:
                vat_rate = taxes[0].amount  # adjust if multiple taxes

            receipt_list.append({
                "VendorCode": product.default_code or "",
                "Name": product.display_name,
                "CdUKDZED": "",
                "CdDKPP": "",
                "GoodsType": "",
                "Barcode": product.barcode or "",
                "UnitType": product.uom_id.name or "шт",
                "Quantity": str((-1 if self.is_refund else 1) * line.qty),
                "Price": f"{line.price_unit:.2f}",
                "Amount": f"{line.price_subtotal:.2f}",
                "DiscountPrc": f"{line.discount:.2f}",
                "DiscountSum": f"{(-1 if self.is_refund else 1) * line.price_unit * line.qty * line.discount / 100:.2f}",
                "VATRate": str(vat_rate),
                "IsPriceIncludeVAT": True,
                "SumVAT": f"{(line.price_subtotal_incl - line.price_subtotal):.2f}",
                "IsExcise": False,
                "OtherParametrs": None,
            })

        return {
            "ReceiptLst": receipt_list,
            "Comment": self.general_customer_note or "",
        }

    def get_fiscal_payments(self):
        self.ensure_one()

        cash = 0
        card = 0

        for payment in self.payment_ids:
            if payment.payment_method_id.is_cash_count:
                cash += (-1 if self.is_refund else 1) * payment.amount
            else:
                card += (-1 if self.is_refund else 1) * payment.amount

        payload = {
            "SumCash": f"{cash:.2f}",
            "SumPayByCard": f"{card:.2f}",
            "SumPayByCredit": "0.00",
            "SumPayByCertificate": "0.00",
            "SumPayCheck": f"{(-1 if self.is_refund else 1) * self.amount_total:.2f}",
            "TerminalID": "",
            "ApprovalCode": "",
            "RRN": "",
            "IssuerName": "",
            "PAN": "",
            "TransactionDate": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "AcquireName": "",
            "InvoiceNumber": self.pos_reference or "",
        }

        if self.partner_id.email:
            payload["CustomerEmail"] = self.partner_id.email

        return payload

    def get_fiscal_payload(self):
        self.ensure_one()

        payload =  {
            "goods": self.get_fiscal_order_lines(),
            "payments": self.get_fiscal_payments()
        }

        if self.is_refund:
            payload["is_refund"] = True
            payload["original_receipt_fiscal_id"] = str(self.get_original_fiscal_id())

        return payload
    
    
    def get_original_fiscal_id(self):
        self.ensure_one()

        if not self.refunded_order_id:
            return

        original_order = self.env['pos.order'].browse(self.refunded_order_id.id)

        if original_order and original_order.exists():
            return original_order.document_fiscal_id


    @api.model
    def save_unique_fiscal_id(self, document_fiscal_id:str, existing_order):
        """Updates document_fiscal_id in pos.order

        :param str document_fiscal_id: the fiscal id to store
        :param existing_order: order to be updated or False.
        :type existing_order: pos.order.
        :returns: True of updated pos.order
        :rtype: bool
        """

        # If the order is belonging to another session, it must be moved to the current session first
        existing_order.write({'document_fiscal_id': document_fiscal_id})

        return True