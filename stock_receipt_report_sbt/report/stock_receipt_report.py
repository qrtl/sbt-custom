# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockReceiptReport(models.TransientModel):
    _name = "stock.receipt.report"

    report_type = fields.Selection(
        [("incoming", "Purchase"), ("outgoing", "Return")], "Report Type"
    )
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("in_payment", "In Payment"),
            ("paid", "Paid"),
        ],
        string="Status",
    )
    filter_so_partner_ids = fields.Many2many("res.partner", "srr_parter_rel")
    filter_picking_partner_ids = fields.Many2many("res.partner", "srr_supplier_rel")
    filter_product_ids = fields.Many2many("product.product",)

    @api.multi
    def print_report(self, report_type):
        report_name = "stock_receipt_report_sbt.stock_receipt_report_xlsx"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, config=False)
        )
