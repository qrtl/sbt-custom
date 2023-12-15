# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        super(SaleOrder, self).action_confirm()

        for order in self:
            logging.info("Processing Order: %s", order.name)
            if order.ebisumart_send_date:
                for line in order.order_line:
                    line.move_ids.write({'date_expected': order.ebisumart_send_date})
        return
