# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import api, fields, models


class AccountPaymentReport(models.TransientModel):
    _name = "account.payment.report"

    report_type = fields.Selection(
        [("inbound", "Refund"), ("outbound", "Payment")], "Report Type"
    )
    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    filter_order_ids = fields.Many2many("sale.order",)
    filter_partner_ids = fields.Many2many("res.partner",)
    filter_journal_ids = fields.Many2many("account.journal",)

    @api.multi
    def print_report(self, report_type):
        report_name = "account_payment_report_sbt.account_payment_report_xlsx"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, config=False)
        )
