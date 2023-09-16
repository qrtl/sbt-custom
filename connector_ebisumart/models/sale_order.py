# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        # force assign schedule_date with SEND_DATE of ebisumart
        for order in self:
            order.picking_ids.write({'scheduled_date': self.ebisumart_send_date})
        return res
