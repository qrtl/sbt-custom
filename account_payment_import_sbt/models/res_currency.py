# Copyright 2020 Quartile Limited

from odoo import api, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        return (
            self.env.context.get("custom_exchange_rate")
            if self.env.context.get("custom_exchange_rate")
            else super()._get_conversion_rate(from_currency, to_currency, company, date)
        )
