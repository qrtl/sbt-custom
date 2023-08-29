# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ebisumart_id = fields.Integer(string="TORHIKISAKI ID")
    sales_partner = fields.Many2one('res.partner')
