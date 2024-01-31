# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    mid = fields.Char(string="MID")
