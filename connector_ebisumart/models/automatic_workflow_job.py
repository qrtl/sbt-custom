# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AutomaticWorkflowJob(models.Model):
    _inherit = 'automatic.workflow.job'

    def _do_validate_picking(self, picking):
        super()._do_validate_picking(picking)
        if picking.sale_id.cancel_in_ebisumart:
            return_date = picking.sale_id.ebisumart_cancel_date
            self.create_return_picking(picking.sale_id, return_date)
            purchase_order = self.env['purchase.order'].search(
                [('origin', '=', picking.sale_id.name)]
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

    def create_return_picking(self, order, return_date):
        for picking in order.picking_ids.filtered(lambda r: r.state == 'done'):
            # Create the reverse transfer
            stock_return_picking = self.env['stock.return.picking']
            return_wizard = stock_return_picking.with_context(
                active_ids=picking.ids, active_id=picking.ids[0]
            ).create({})
            return_result = return_wizard.create_returns()

            # Usually, the return_result contains information
            # about the newly created return picking(s)
            if return_result and 'res_id' in return_result:
                new_return_picking = self.env['stock.picking'].browse(
                    return_result['res_id']
                )
                new_return_picking.write({'scheduled_date': return_date})

                # Validate (confirm) the return picking
                if new_return_picking.state != 'done':
                    wiz = self.env['stock.immediate.transfer'].create({
                        'pick_ids': [(4, new_return_picking.id)]
                    })
                    wiz.process()

    def create_credit_note(self, order, invoice_type):
        for invoice in order.invoice_ids.filtered(
            lambda r: r.state not in ['cancel', 'draft'] and r.type == invoice_type
        ):
            # Create the refund (credit note)
            account_invoice_refund = self.env['account.invoice.refund']
            refund_wizard = account_invoice_refund.create({
                'description': 'Credit Note',
                'filter_refund': 'refund',  # refund the entire invoice
            })
            refund_result = refund_wizard.with_context(
                active_ids=invoice.ids
            ).invoice_refund()
            if refund_result and refund_result.get('domain'):
                # Search for the newly created credit note
                credit_notes = self.env['account.invoice'].search(
                    refund_result.get('domain')
                )
                for credit_note in credit_notes:
                    if credit_note.state == 'draft':
                        credit_note.action_invoice_open()
