# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    unified_number = fields.Char("Unified number")
