# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.component.core import Component


class EbisumartProduct(models.Model):
    _name = 'ebisumart.product.product'
    _inherit = 'ebisumart.binding'
    _inherits = {'product.product': 'odoo_id'}
    _description = 'Ebisumart Product'

    odoo_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='cascade'
    )
    created_at = fields.Date('Created At (on Ebisumart)')
    updated_at = fields.Date('Updated At (on Ebisumart)')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ebisumart_bind_ids = fields.One2many(
        comodel_name='ebisumart.product.product',
        inverse_name='odoo_id',
        string='Ebisumart Bindings',
    )
    torihikisaki_id = fields.Integer(
        "Partner ID on ebisumart", readonly=True, store=True
    )


class ProductAdapter(Component):
    _name = 'ebisumart.product.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.product.product']

    # Add methods for communicating with the Ebisumart API

    def search(self, attributes=None, filters=None):
        # Call the base method with the "/items" endpoint
        last_fetch_date = self.backend_record.last_fetch_product_date
        if last_fetch_date:
            filters = self._get_date_filters(last_fetch_date)
        self.backend_record.last_fetch_product_date = fields.datetime.now()
        attributes = ['ITEM_ID']
        return super().search("/items", attributes=attributes, filters=filters)

    def read(self, external_id, attributes=None):
        """ Returns the detailed information for an existing product."""
        # Adjust the URL endpoint accordingly
        if not attributes:
            attributes = [
                'ITEM_NAME', 'ITEM_ID', 'ITEM_CD', 'TEIKA', 'TORIHIKISAKI_ID',
                'SHIRE_PRICE', 'REGIST_DATE', 'UPDATE_DATE'
            ]
        return super().read(f"/items/{external_id}", attributes=attributes)
