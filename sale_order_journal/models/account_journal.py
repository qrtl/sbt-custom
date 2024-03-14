# Copyright 2023 Quartile Limited
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    account_receivable_id = fields.Many2one("account.account", string="Advance Received Account", domain="[('internal_type', '=', 'receivable'),('deprecated', '=', False)]")
