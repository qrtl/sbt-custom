# Copyright 2023 Quartile Limited

from odoo.addons.component.core import Component
from odoo import fields, models


# Not used at the moment and all product will assign to default category. 
# This is for the future development
class EbisumartProductCategory(models.Model):
    _name = 'ebisumart.product.category'
    _inherit = 'ebisumart.binding'
    _inherits = {'product.category': 'odoo_id'}
    _description = 'Ebisumart Product Category'

    odoo_id = fields.Many2one(comodel_name='product.category', string='Product Category',
                             required=True, ondelete='cascade')
    category_code = fields.Char()
    ebisumart_parent_id = fields.Many2one(
        comodel_name='ebisumart.product.category',
        string='Ebisumart Parent Category',
        ondelete='cascade',
    )
    ebisumart_child_ids = fields.One2many(
        comodel_name='ebisumart.product.category',
        inverse_name='ebisumart_parent_id',
        string='Ebisumart Child Categories',
    )
    
class ProductCategory(models.Model):
    _inherit = 'product.category'

    ebisumart_bind_ids = fields.One2many(
        comodel_name='ebisumart.product.category',
        inverse_name='odoo_id',
        string="Ebisumart Bindings",
    )

class ProductAdapter(Component):
    _name = 'ebisumart.product.category.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.product.category']
    
    def search(self, attributes=None, filters=None):
        """ Search for list of categories. """
        attributes = ['CATEGORY_ID']
        return super().search("/categories", attributes=attributes, filters=filters)

    def read(self, external_id, attributes=None):
        """ Return details for a specific category. """
        if not attributes:
            attributes = ['CATEGORY_ID', 'CATEGORY_NAME', 'CATEGORY_PARENT']  # Define default attributes to fetch
        return super().read("/categories/%s" % external_id, attributes=attributes)

    def tree(self, parent_id=None):
        """ Returns a tree of product categories """
        if parent_id:
            categories = self._get_child_categories(parent_id)
        else:
            categories = self.search()

        for category in categories:
            child_categories = self._get_child_categories(category['CATEGORY_ID'])
            if child_categories:
                category['children'] = self.tree(category['CATEGORY_ID'])
        return categories

    def _get_child_categories(self, category_id):
        """ Helper function to fetch child categories for a given category_id. """
        return self.read("/categories/%s/child_categories" % category_id)
