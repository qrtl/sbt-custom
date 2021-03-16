# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import api, fields, models


class AccountPaymentReportWizard(models.TransientModel):
    _name = "account.payment.report.wizard"

    report_type = fields.Selection(
        [("inbound", "Payment"), ("outbound", "Refund")],
        "Report Type",
        default="inbound",
    )
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    order_ids = fields.Many2many("sale.order", string="Sale Order Code",)
    partner_ids = fields.Many2many(
        "res.partner", domain=[("customer", "=", True)], string="Customer Code",
    )
    journal_ids = fields.Many2many(
        "account.journal",
        domain=[("type", "in", ("bank", "cash"))],
        string="Payment Method",
    )

    def _prepare_account_payment_report(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "report_type": self.report_type,
            "filter_order_ids": [(6, 0, self.order_ids.ids)],
            "filter_partner_ids": [(6, 0, self.partner_ids.ids)],
            "filter_journal_ids": [(6, 0, self.journal_ids.ids)],
        }

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _export(self, report_type):
        model = self.env["account.payment.report"]
        report = model.create(self._prepare_account_payment_report())
        return report.print_report(report_type)
