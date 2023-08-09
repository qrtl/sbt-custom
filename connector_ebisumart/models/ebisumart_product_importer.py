# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from ..components.mapper import normalize_datetime


class ProductImportMapper(Component):
    _name = 'ebisumart.product.product.import.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = ['ebisumart.product.product']

    direct = [
        ("ITEM_NAME", "name"),
        ("ITEM_CD", "default_code"),
        ("TEIKA", "list_price"),
        ("SHIIRE_PRICE", "standard_price"),
        (normalize_datetime('REGIST_DATE'), 'created_at'),
        (normalize_datetime('UPDATE_DATE'), 'updated_at'),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the product to an existing one with the same code """
        product = self.env['product.product'].search(
            [('default_code', '=', record['ITEM_CD'])], limit=1)
        if product:
            return {'odoo_id': product.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

class ProductBatchImporter(Component):
    """ Import the Ebisumart Products.

    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _name = 'ebisumart.product.product.batch.importer'
    _inherit = 'ebisumart.delayed.batch.importer'
    _apply_on = ['ebisumart.product.product']

    def run(self, filters=None):
        """ Run the synchronization """
        external_datas = self.backend_adapter.search(filters)
        external_ids = [item["ITEM_ID"] for item in external_datas]
        for external_id in external_ids:
            self._import_record(external_id)

class EbisumartProductImporter(Component):
    _name = 'ebisumart.product.product.importer'
    _inherit = 'ebisumart.importer'
    _apply_on = 'ebisumart.product.product'
