# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    write_off_account_id = fields.Many2one(
        "account.account",
        string="Write-Off Account",
        related="company_id.write_off_account_id",
        readonly=False,
    )
