# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


from odoo import fields, models

class EbisumartProduct(models.Model):
    _name = 'ebisumart.product.product'
    _inherit = 'ebisumart.binding'
    _inherits = {'product.product': 'odoo_id'}
    _description = 'Ebisumart Product'

    odoo_id = fields.Many2one(comodel_name='product.product', string='Product',
                             required=True, ondelete='cascade')
    created_at = fields.Date('Created At (on Ebisumart)')
    updated_at = fields.Date('Updated At (on Ebisumart)')

    # TODO
    # add related fields depends on requriements

class ProductProduct(models.Model):
    _inherit = 'product.product'

    ebisumart_bind_ids = fields.One2many(
        comodel_name='ebisumart.product.product',
        inverse_name='odoo_id',
        string='Ebisumart Bindings',
    )

class ProductAdapter(Component):
    _name = 'ebisumart.product.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.product.product']
    
    # Add methods for communicating with the Ebisumart API

    def search(self, attributes=None, filters=None):
        # Call the base method with the "/items" endpoint
        attributes = ['ITEM_ID']
        return super().search("/items", attributes=attributes, filters=filters)

    def read(self, external_id, attributes=None):
        """ Returns the detailed information for an existing product."""
        # Adjust the URL endpoint accordingly
        if not attributes:
            attributes = ['ITEM_NAME','ITEM_ID', 'ITEM_CD', 'TEIKA', 'REGIST_DATE', 'UPDATE_DATE']  # Define default attributes to fetch
        return super().read(f"/items/{external_id}", attributes=attributes)
