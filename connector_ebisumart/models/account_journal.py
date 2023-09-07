# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    ebisumart_payment_type = fields.Selection(
        [
            ('credit_card', 'Credit Card'),
            ('payment_slip', 'Payment Slip'),
        ]
    )
