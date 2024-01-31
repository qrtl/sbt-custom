# Copyright 2020 Quartile Limited

from odoo import fields, models


class ErrorLogLine(models.Model):
    _inherit = "error.log.line"

    order_number = fields.Char(string="Order Number")
    invoice_number = fields.Char(string="Invoice Number")
    partner_ref = fields.Char(string="Shop CD")
    # currency_id = fields.Many2one(
    #     "res.currency", default=lambda self: self.env.ref("base.JPY")
    # )
    invoice_amount = fields.Float(string="Invoice Amount")
    total_amount = fields.Float(string="Payment Amount")
    journal = fields.Char(string="Journal")
    warning_log_id = fields.Many2one("error.log", string="Log")
