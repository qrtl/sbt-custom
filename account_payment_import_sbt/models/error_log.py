# Copyright 2020 Quartile Limited

from odoo import fields, models


class ErrorLog(models.Model):
    _inherit = "error.log"

    payment_ids = fields.One2many(
        "account.payment", "log_id", string="Imported Payments"
    )
    warning_log_line_ids = fields.One2many(
        "error.log.line", "warning_log_id", string="Warning Log Lines"
    )
