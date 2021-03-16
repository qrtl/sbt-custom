# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    related_sale_order_id = fields.Many2one(
        "sale.order", compute="_compute_related_sale_order_id", store=True,
    )

    @api.depends("origin", "type")
    def _compute_related_sale_order_id(self):
        for rec in self:
            rec.related_sale_order_id = False
            if rec.origin:
                if rec.type == "out_invoice":
                    rec.related_sale_order_id = self.env["sale.order"].search(
                        [("name", "=", rec.origin)], limit=1
                    )
                elif rec.type == "out_refund":
                    related_invoice = self.env["account.invoice"].search(
                        [("number", "=", rec.origin)], limit=1
                    )
                    if related_invoice and related_invoice.origin:
                        rec.related_sale_order_id = self.env["sale.order"].search(
                            [("name", "=", related_invoice.origin)], limit=1
                        )
