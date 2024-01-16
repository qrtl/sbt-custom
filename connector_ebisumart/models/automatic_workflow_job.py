# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AutomaticWorkflowJob(models.Model):
    _name = 'automatic.workflow.job'
    _inherit = ['order.cancel.process', 'automatic.workflow.job']

    def _do_validate_picking(self, picking):
        super()._do_validate_picking(picking)
        if picking.sale_id.cancel_in_ebisumart:
            return_date = picking.sale_id.ebisumart_cancel_date
            self.create_return_picking(picking.sale_id, return_date)
            purchase_order = self.env['purchase.order'].search(
                [('origin', '=', picking.sale_id.name)], limit=1
                )
            if not purchase_order:
                return
            self.create_return_picking(purchase_order, return_date)

    def _do_validate_invoice(self, invoice):
        super()._do_validate_invoice(invoice)
        sale_orders = invoice.mapped('invoice_line_ids.sale_line_ids.order_id')
        for sale_order in sale_orders:
            if sale_order.cancel_in_ebisumart:
                self.create_credit_note(sale_order, invoice_type="out_invoice")
                purchase_order = self.env['purchase.order'].search(
                    [('origin', '=', sale_order.name)],
                    limit=1, order="id desc"
                )
                if not purchase_order:
                    continue
                self.create_credit_note(purchase_order, invoice_type="in_invoice")
