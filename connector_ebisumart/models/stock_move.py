# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        res = super(StockMove, self)._get_new_picking_values()
        if self.group_id.sale_id.ebisumart_send_date:
            res.update({'scheduled_date': self.group_id.sale_id.ebisumart_send_date})
        return res
