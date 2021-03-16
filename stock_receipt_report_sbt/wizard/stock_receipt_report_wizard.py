# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockReceiptReportWizard(models.TransientModel):
    _name = "stock.receipt.report.wizard"

    report_type = fields.Selection(
        [("incoming", "Purchase"), ("outgoing", "Return")],
        "Report Type",
        default="incoming",
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
    so_partner_ids = fields.Many2many(
        "res.partner",
        "srrw_parter_rel",
        domain=[("customer", "=", True)],
        string="Customer Code",
    )
    picking_partner_ids = fields.Many2many(
        "res.partner",
        "srrw_supplier_rel",
        domain=[("supplier", "=", True)],
        string="Supplier Code",
    )
    product_ids = fields.Many2many(
        "product.product", domain=[("purchase_ok", "=", True)], string="Product Code",
    )

    def _prepare_stock_receipt_report(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "state": self.state,
            "report_type": self.report_type,
            "filter_so_partner_ids": [(6, 0, self.so_partner_ids.ids)],
            "filter_picking_partner_ids": [(6, 0, self.picking_partner_ids.ids)],
            "filter_product_ids": [(6, 0, self.product_ids.ids)],
        }

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _export(self, report_type):
        model = self.env["stock.receipt.report"]
        report = model.create(self._prepare_stock_receipt_report())
        return report.print_report(report_type)
