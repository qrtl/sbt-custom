from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ProductImportMapper(Component):
    _name = 'ebisumart.product.product.import.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = ['ebisumart.product.product']

    # TODO :     categ, special_price => minimal_price
    direct = []

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the product to an existing one with the same code """
        product = self.env['product.product'].search(
            [('default_code', '=', record['sku'])], limit=1)
        if product:
            return {'odoo_id': product.id}

    @mapping
    def external_id(self, record):
        return

    @mapping
    def is_active(self, record):
        return

    @mapping
    def price(self, record):
        return

    @mapping
    def type(self, record):
        return

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
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        external_ids = self.backend_adapter.search(filters,
                                                   from_date=from_date,
                                                   to_date=to_date)
        for external_id in external_ids:
            self._import_record(external_id)

class EbisumartProductImporter(Component):
    _name = 'ebisumart.product.product.importer'
    _inherit = 'ebisumart.importer'
    _apply_on = 'ebisumart.product.product'

    def run(self, external_id, force=False):
        """ Run the synchronization """
