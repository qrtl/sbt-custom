# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    journal_id = fields.Many2one("account.journal", "Payment Method", required=True)

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()  
        if self.journal_id.account_receivable_id:
            invoice_vals.update({
                'account_id': self.journal_id.account_receivable_id.id,
            })
        return invoice_vals
