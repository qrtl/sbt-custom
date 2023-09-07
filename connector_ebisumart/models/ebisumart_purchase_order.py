# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.component.core import Component


class EbisumartPurchaseOrder(models.Model):
    _name = 'ebisumart.purchase.order'
    _inherit = 'ebisumart.binding'
    _inherits = {'purchase.order': 'odoo_id'}
    _description = 'Ebisumart Purchase Order'

    odoo_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        required=True,
        ondelete='cascade'
    )
    ebisumart_order_line_ids = fields.One2many(
        comodel_name='ebisumart.purchase.order.line',
        inverse_name='ebisumart_order_id',
        string='Ebisumart Order Lines'
    )
    created_at = fields.Date('Created At (on Ebisumart)')
    updated_at = fields.Date('Updated At (on Ebisumart)')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ebisumart_bind_ids = fields.One2many(
        comodel_name='ebisumart.purchase.order',
        inverse_name='odoo_id',
        string='Ebisumart Bindings',
    )
    cancel_in_ebisumart = fields.Boolean()

    def _after_import(self):
        if self.state == 'purchase':
            return
        # Confirm the purchase order.
        self.button_confirm()

        # Validate the associated receipt (stock picking).
        for picking in self.picking_ids:
            wiz = self.env['stock.immediate.transfer'].create(
                {'pick_ids': [(4, picking.id)]}
            )
            wiz.process()

        po_invoice = {
            'partner_id': self.partner_id.id,
            'account_id': self.partner_id.property_account_payable_id.id,
            'state': 'draft',
            'type': 'in_invoice',
            'purchase_id': self.id,
        }

        inv = self.env['account.invoice'].create(po_invoice)
        inv.purchase_order_change()
        inv.action_invoice_open()


class EbisumartPurchaseOrderLine(models.Model):
    _name = 'ebisumart.purchase.order.line'
    _inherit = 'ebisumart.binding'
    _description = 'Ebisumart Purchase Order Line'
    _inherits = {'purchase.order.line': 'odoo_id'}

    ebisumart_order_id = fields.Many2one(
        comodel_name='ebisumart.purchase.order',
        string='Ebisumart Purchase Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    odoo_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Purchase Order Line',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        related='ebisumart_order_id.backend_id',
        string='Ebisumart Backend',
        readonly=True,
        store=True,
        required=False,
    )

    @api.model
    def create(self, vals):
        ebisumart_order_id = vals['ebisumart_order_id']
        binding = self.env['ebisumart.purchase.order'].browse(ebisumart_order_id)
        vals['order_id'] = binding.odoo_id.id
        vals['date_planned'] = binding.odoo_id.date_order
        binding = super(EbisumartPurchaseOrderLine, self).create(vals)
        return binding


class PurchaseAdapter(Component):
    _name = 'ebisumart.purchase.order.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.purchase.order']

    def search(self, attributes=None, filters=None):
        # Define default attributes to fetch
        attributes = [
            'ORDER_NO', 'KESSAI_ID', 'ORDER_DISP_NO',
            'SEND_DATE', 'CANCEL_DATE', 'FREE_ITEM1'
        ]
        return super().search("/orders", attributes=attributes, filters=filters)

    def read(self, external_id, attributes=None):
        """ Returns the detailed information for an existing product."""
        # Adjust the URL endpoint accordingly
        if not attributes:
            attributes = [
                'ORDER_NO', 'KESSAI_ID', 'ORDER_DISP_NO', 'SEND_DATE',
                'order_details(ORDER_D_NO,ITEM_ID,ITEM_NAME,QUANTITY,SHIRE_PRICE)',
                'REGIST_DATE', 'UPDATE_DATE'
            ]
        return super().read(f"/orders/{external_id}", attributes=attributes)
