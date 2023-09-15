# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api
import logging


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for picking in self.picking_ids:
            picking.write({'scheduled_date': self.ebisumart_send_date})
        return res
