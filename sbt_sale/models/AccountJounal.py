# Part of Pactera. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountJournalEtx(models.Model):
    _inherit = "account.journal"

    code = fields.Char(
        string="Short Code",
        required=True,
        size=20,
        help="The journal entries of this journal will be named using this prefix.",
    )


class AccountInvoicelEtx(models.Model):
    _inherit = "account.invoice"

    def create_vendor_invoice(self, purchase_id):
        purchase_order = self.env["purchase.order"].search(
            [("id", "=", purchase_id)], limit=1
        )
        if purchase_order:
            vendor = purchase_order.partner_id
            # create the vendor bill
            vendor_bill1 = self.env["account.invoice"].create(
                {
                    "partner_id": vendor.id,
                    "purchase_id": purchase_order.id,
                    "account_id": vendor.property_account_payable_id.id,
                    "type": "in_invoice",
                }
            )
            vendor_bill1.purchase_order_change()
            return vendor_bill1.id
        return False

    def create_invoice_refund(
        self, invoice_ids, filter_refund, description, date_invoice, date
    ):
        refund_invoice = self.env["account.invoice.refund"].create(
            {
                "filter_refund": filter_refund,
                "description": description,
                "date_invoice": date_invoice,
                "date": date,
            }
        )
        # create the vendor bill
        refund_invoice.with_context(active_ids=invoice_ids).invoice_refund()
        refund_invoice = self.env["account.invoice"].search(
            [("name", "=", description)], limit=1, order="id desc"
        )
        if refund_invoice:
            return refund_invoice.id
        return False


class StockPickingEtx(models.Model):
    _inherit = "stock.picking"

    def return_stock_picking(self, picking_ids):
        stock_return_picking = (
            self.env["stock.return.picking"]
            .with_context(active_ids=picking_ids, active_id=picking_ids[0])
            .create({})
        )
        stock_return_picking_action = stock_return_picking.create_returns()
        return stock_return_picking_action["res_id"]
