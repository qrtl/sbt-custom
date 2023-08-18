# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import fields, models, api


class EbisumartPurchaseOrder(models.Model):
    _name = 'ebisumart.purchase.order'
    _inherit = 'ebisumart.binding'
    _inherits = {'purchase.order': 'odoo_id'}
    _description = 'Ebisumart Purchase Order'

    odoo_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order',
                             required=True, ondelete='cascade')
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

class EbisumartPurchaseOrderLine(models.Model):
    _name = 'ebisumart.purchase.order.line'
    _inherit = 'ebisumart.binding'
    _description = 'Ebisumart Purchase Order Line'
    _inherits = {'purchase.order.line': 'odoo_id'}

    ebisumart_order_id = fields.Many2one(comodel_name='ebisumart.purchase.order',
                                       string='Ebisumart Purchase Order',
                                       required=True,
                                       ondelete='cascade',
                                       index=True)
    odoo_id = fields.Many2one(comodel_name='purchase.order.line',
                              string='Purchase Order Line',
                              required=True,
                              ondelete='cascade')
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
        binding = super(EbisumartPurchaseOrderLine, self).create(vals)
        return binding
    
class ProductAdapter(Component):
    _name = 'ebisumart.purchase.order.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.purchase.order']
    
    # Add methods for communicating with the Ebisumart API

    def search(self, attributes=None, filters=None):
        # Call the base method with the "/orders" endpoint
        attributes = ['ORDER_NO','KESSAI_ID','ORDER_DISP_NO','AUTHORY_DATE','SEND_DATE','CANCEL_DATE']
        filters = [
            {
                "column":"KESSAI_ID",
                "operator":"equals",
                "value": 61,
        }
        ]
        return super().search("/orders", attributes=attributes, filters=filters)

    def read(self, external_id, attributes=None):
        """ Returns the detailed information for an existing product."""
        # Adjust the URL endpoint accordingly
        if not attributes:
            attributes = ['ORDER_NO','KESSAI_ID','ORDER_DISP_NO','SEND_DATE','order_details(ORDER_D_NO,ITEM_ID,ITEM_NAME,QUANTITY,SHIRE_PRICE)', 'REGIST_DATE', 'UPDATE_DATE']  # Define default attributes to fetch
        return super().read(f"/orders/{external_id}", attributes=attributes)
