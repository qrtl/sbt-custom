# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    company_name = fields.Char("Company name")
