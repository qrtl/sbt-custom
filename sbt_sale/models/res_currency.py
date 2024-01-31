# Part of Pactera. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    rate = fields.Float(
        compute="_compute_current_rate",
        string="Current Rate",
        digits=(12, 12),
        help="The rate of the currency to the currency of rate 1.",
    )
    rounding = fields.Float(string="Rounding Factor", digits=(12, 12), default=0.01)


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"
    rate = fields.Float(
        digits=(12, 12),
        default=1.0,
        help="The rate of the currency to the currency of rate 1",
    )
