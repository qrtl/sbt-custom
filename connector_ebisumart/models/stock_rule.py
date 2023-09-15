# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_purchase_order(self, product_id, product_qty, product_uom, origin, values, partner):
        vals = super()._prepare_purchase_order(product_id, product_qty, product_uom, origin, values, partner)
        vals["name"] = 'P_'+ origin
        sale_order = self.env['sale.order'].search([('name','=', origin)], limit=1)
        vals["ebisumart_send_date"] = sale_order.ebisumart_send_date
        return vals
