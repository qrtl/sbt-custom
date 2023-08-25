# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import fields, models, api


class EbisumartSaleOrder(models.Model):
    _name = 'ebisumart.sale.order'
    _inherit = 'ebisumart.binding'
    _inherits = {'sale.order': 'odoo_id'}
    _description = 'Ebisumart Sale Order'

    odoo_id = fields.Many2one(comodel_name='sale.order', string='Sale Order',
                             required=True, ondelete='cascade')
    ebisumart_order_line_ids = fields.One2many(
        comodel_name='ebisumart.sale.order.line',
        inverse_name='ebisumart_order_id',
        string='Ebisumart Order Lines'
    )
    created_at = fields.Date('Created At (on Ebisumart)')
    updated_at = fields.Date('Updated At (on Ebisumart)')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ebisumart_bind_ids = fields.One2many(
        comodel_name='ebisumart.sale.order',
        inverse_name='odoo_id',
        string='Ebisumart Bindings',
    )
    cancel_in_ebisumart = fields.Boolean()

class EbisumartsaleOrderLine(models.Model):
    _name = 'ebisumart.sale.order.line'
    _inherit = 'ebisumart.binding'
    _description = 'Ebisumart Sale Order Line'
    _inherits = {'sale.order.line': 'odoo_id'}

    ebisumart_order_id = fields.Many2one(comodel_name='ebisumart.sale.order',
                                       string='Ebisumart Sale Order',
                                       required=True,
                                       ondelete='cascade',
                                       index=True)
    odoo_id = fields.Many2one(comodel_name='sale.order.line',
                              string='Sale Order Line',
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
        binding = self.env['ebisumart.sale.order'].browse(ebisumart_order_id)
        vals['order_id'] = binding.odoo_id.id
        binding = super(EbisumartsaleOrderLine, self).create(vals)
        return binding
    
class ProductAdapter(Component):
    _name = 'ebisumart.sale.order.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.sale.order']
    
    # Add methods for communicating with the Ebisumart API

    def search(self, attributes=None, filters=None):
        # Call the base method with the "/orders" endpoint
        attributes = ['ORDER_NO','KESSAI_ID','ORDER_DISP_NO','AUTHORY_DATE','SEND_DATE','CANCEL_DATE']
        return super().search("/orders", attributes=attributes, filters=filters)

    def read(self, external_id, attributes=None):
        """ Returns the detailed information for an existing product."""
        # Adjust the URL endpoint accordingly
        if not attributes:
            attributes = ['ORDER_NO','KESSAI_ID','ORDER_DISP_NO','SEND_DATE','order_details(ORDER_D_NO,ITEM_ID,ITEM_NAME,QUANTITY,TEIKA)', 'REGIST_DATE', 'UPDATE_DATE']  # Define default attributes to fetch
        return super().read(f"/orders/{external_id}", attributes=attributes)