# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockDeliveryReportWizard(models.TransientModel):
    _name = "stock.delivery.report.wizard"

    report_type = fields.Selection(
        [("outgoing", "Delivery"), ("incoming", "Return")],
        "Report Type",
        default="outgoing",
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
    picking_partner_ids = fields.Many2many(
        "res.partner", domain=[("customer", "=", True)], string="Customer Code",
    )

    def _prepare_stock_delivery_report(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "state": self.state,
            "report_type": self.report_type,
            "filter_picking_partner_ids": [(6, 0, self.picking_partner_ids.ids)],
        }

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _export(self, report_type):
        model = self.env["stock.delivery.report"]
        report = model.create(self._prepare_stock_delivery_report())
        return report.print_report(report_type)
