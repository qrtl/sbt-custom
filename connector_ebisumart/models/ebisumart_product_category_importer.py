from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError


# Not used at the moment and all product will assign to default category. 
# This is for the future development
class ProductCategoryMapper(Component):
    _name = 'ebisumart.product.category.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = 'ebisumart.product.category'

    direct = [
        ('CATEGORY_NAME', 'name'),
        ('CATEGORY_CD', 'category_code')
    ]

    @mapping
    def parent_id(self, record):
        if not record['CATEGORY_PARENT']:
            return
        parent_binding = self.env['ebisumart.product.category'].search([
            ('category_code', '=', record['CATEGORY_PARENT']),
        ], limit=1)
        if not parent_binding:
            raise MappingError("The product category with "
                               "ebisumart id %s is not imported." %
                               record['CATEGORY_PARENT'])
        parent = parent_binding.odoo_id
        return {'parent_id': parent.id, 'ebisumart_parent_id': parent_binding.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class ProductCategoryBatchImporter(Component):
    """ Import the ebisumart Product Categories.

    For every product category in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """
    _name = 'ebisumart.product.category.batch.importer'
    _inherit = 'ebisumart.delayed.batch.importer'
    _apply_on = ['ebisumart.product.category']

    def _import_record(self, external_id, job_options=None):
        """ Delay a job for the import """
        super(ProductCategoryBatchImporter, self)._import_record(
            external_id, job_options=job_options
        )

    def run(self, filters=None):
        """ Run the synchronization """
        # Retrieve the hierarchical structure of categories
        category_tree = self.backend_adapter.tree()

        # Use a queue to process categories level by level
        categories_to_process = category_tree
        while categories_to_process:
            next_level_categories = []
            for category in categories_to_process:
                # Import current category
                self._import_record(category['CATEGORY_ID'])
                
                # Queue children for processing in the next iteration
                next_level_categories.extend(category.get('children', []))
            
            # Replace the queue with the next level categories
            categories_to_process = next_level_categories


class ProductCategoryImporter(Component):
    _name = 'ebisumart.product.category.importer'
    _inherit = 'ebisumart.importer'
    _apply_on = ['ebisumart.product.category']

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.ebisumart_record
        # import parent category
        # the root category has a 0 parent_id or might not have a parent
        parent_code = record.get('CATEGORY_PARENT')
        if not parent_code:
            return  # If no parent category, just return

        filters = {'CATEGORY_CD': parent_code}
        parent_records = self.search(filters=filters)
        # Assuming the code is unique and returns only one record
        parent_record = parent_records[0]
        self._import_dependency(parent_record.get('CATEGORY_ID'), self.model)

    def _create(self, data):
        binding = super(ProductCategoryImporter, self)._create(data)
        self.backend_record.add_checkpoint(binding)
        return binding
