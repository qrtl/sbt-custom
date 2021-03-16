# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    report_date_format = fields.Char(
        string="Report Date Format", default="YYYY/MM/dd", required=True,
    )
