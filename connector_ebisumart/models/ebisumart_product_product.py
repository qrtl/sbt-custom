# Copyright 2023 Quartile Limited

from odoo.addons.component.core import Component


from odoo import fields, models

class EbisumartProduct(models.Model):
    _name = 'ebisumart.product.product'
    _inherit = 'ebisumart.binding'
    _inherits = {'product.product': 'odoo_id'}
    _description = 'Ebisumart Product'

    odoo_id = fields.Many2one(comodel_name='product.product', string='Product',
                             required=True, ondelete='cascade')
    # Add any additional fields that are relevant to the product

class ProductAdapter(Component):
    _name = 'ebisumart.product.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.product.product']
    
    # Add methods for communicating with the Ebisumart API
