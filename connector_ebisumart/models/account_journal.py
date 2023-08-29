from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    ebisumart_payment_type = fields.Selection([
            ('credit_card', 'Credit Card'),
            ('playment_slip', 'Payment Slip'),
        ])
