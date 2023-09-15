# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ebisumart_send_date = fields.Datetime()

    @api.multi
    def _create_picking(self):
        res = super(PurchaseOrder, self)._create_picking()
        for order in self:
            if order.picking_ids:
                order.picking_ids.write({"scheduled_date": order.ebisumart_send_date})
        return res
