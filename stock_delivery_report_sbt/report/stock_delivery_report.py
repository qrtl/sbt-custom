# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockDeliveryReport(models.TransientModel):
    _name = "stock.delivery.report"

    report_type = fields.Selection(
        [("outgoing", "Delivery"), ("incoming", "Return")], "Report Type"
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
    filter_picking_partner_ids = fields.Many2many("res.partner",)

    @api.multi
    def print_report(self, report_type):
        report_name = "stock_delivery_report_sbt.stock_delivery_report_xlsx"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, config=False)
        )
