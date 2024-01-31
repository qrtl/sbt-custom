# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import _, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    ip_exchange_rate = fields.Float(
        "Import Exchange Rate", copy=False, digits=(12, 12), default=1.0
    )
    is_imported = fields.Boolean("Imported Payment", readonly=True,)
    log_id = fields.Many2one("error.log", string="Log")

    def _check_open_invoice(self, invoices):
        open_invoices = invoices.filtered(lambda a: a.state == "open")
        for invoice in open_invoices:
            for payment in invoice.payment_ids:
                order_lines = (
                    invoice.invoice_line_ids.mapped("sale_line_ids")
                    if "out" in invoice.type
                    else invoice.invoice_line_ids.mapped("purchase_line_id")
                )
                self.env["error.log.line"].create(
                    {
                        "invoice_number": invoice.number,
                        "partner_ref": invoice.partner_id.ref,
                        "invoice_amount": invoice.residual,
                        "order_number": ",".join(
                            order_lines.mapped("order_id").mapped("name")
                        ),
                        "error_message": _(
                            "Invoice %s is still open." % invoice.number
                        ),
                        "warning_log_id": payment.log_id.id,
                    }
                )

    def cron_validate_payment(self, limit):
        processed_invoice = self.env["account.invoice"]
        payments = self.search(
            [("state", "=", "draft"), ("is_imported", "=", True)], limit=limit
        )
        for payment in payments:
            if payment._compute_payment_amount() < payment.amount:
                payment.payment_difference_handling = "reconcile"
            payment.with_context(
                custom_exchange_rate=(1 / payment.ip_exchange_rate) or False
            ).action_validate_invoice_payment()
            processed_invoice += payment.invoice_ids
        self._check_open_invoice(processed_invoice)
