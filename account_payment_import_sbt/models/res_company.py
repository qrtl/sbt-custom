# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.company"

    write_off_account_id = fields.Many2one(
        "account.account", string="Write-Off Account"
    )
