# Part of Pactera. See LICENSE file for full copyright and licensing details.
from datetime import date

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    exchange_rate = fields.Float(
        "Exchange Rate",
        states={"draft": [("readonly", False)]},
        copy=False,
        readonly=True,
        digits=(12, 12),
    )

    @api.multi
    def action_invoice_open(self):
        jpy_currency_id = None
        jpy_currency = self.env.ref("base.JPY")
        if jpy_currency and jpy_currency.id:
            jpy_currency_id = jpy_currency.id
            jpy_rate = (
                self.env["res.currency.rate"]
                .search(
                    [("currency_id", "=", jpy_currency_id)], order="name desc", limit=1
                )
                .rate
            )
            for rec in self:
                current_order = None
                if rec.type:
                    if rec.type == "in_invoice" or rec.type == "out_invoice":
                        current_order = self.env["sale.order"].search(
                            [("name", "=", rec.origin)], limit=1
                        )
                    elif rec.type == "in_refund" or rec.type == "out_refund":
                        refunded_invoice = self.env["account.invoice"].browse(
                            rec.refund_invoice_id.id
                        )
                        if refunded_invoice and refunded_invoice.id:
                            current_order = self.env["sale.order"].search(
                                [("name", "=", refunded_invoice.origin)], limit=1
                            )
                if current_order and current_order.id:
                    if rec.exchange_rate and rec.currency_id.id != jpy_currency_id:
                        currency_date = rec.date_invoice
                        if not currency_date:
                            currency_date = date.today()
                        new_rate = jpy_rate / rec.exchange_rate
                        exist_currency_rate = self.env["res.currency.rate"].search(
                            [
                                ("name", "=", currency_date),
                                ("currency_id", "=", rec.currency_id.id),
                            ],
                            limit=1,
                        )
                        if exist_currency_rate and exist_currency_rate.id:
                            exist_currency_rate.write({"rate": new_rate})
                        else:
                            self.env["res.currency.rate"].create(
                                {
                                    "name": currency_date,
                                    "rate": new_rate,
                                    "currency_id": rec.currency_id.id,
                                }
                            )
        return super(AccountInvoice, self).action_invoice_open()
