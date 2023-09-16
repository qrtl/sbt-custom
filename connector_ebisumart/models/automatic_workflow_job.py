# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AutomaticWorkflowJob(models.Model):
    _inherit = 'automatic.workflow.job'

    def _do_validate_sale_order(self, sale):
        super()._do_validate_sale_order(sale)
        # Search purchase order
        po = self.env['purchase.order'].search([('origin', '=', sale.name)])
        # map data_planned
        for line in po.order_line:
            line.date_planned = po.date_order
        # Confirm the purchase order.
        po.button_confirm()
        # Validate the associated receipt (stock picking).
        for picking in po.picking_ids:
            wiz = self.env['stock.immediate.transfer'].create(
                {'pick_ids': [(4, picking.id)]}
            )
            wiz.process()

        po_invoice = {
            'partner_id': po.partner_id.id,
            'account_id': po.partner_id.property_account_payable_id.id,
            'state': 'draft',
            'type': 'in_invoice',
            'purchase_id': po.id,
        }

        inv = self.env['account.invoice'].create(po_invoice)
        inv.purchase_order_change()
        inv.action_invoice_open()
