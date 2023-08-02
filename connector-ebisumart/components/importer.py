from odoo.addons.component.core import AbstractComponent

class EbisumartImporter(AbstractComponent):
    _name = 'ebisumart.importer'
    _inherit = ['base.importer', 'base.ebisumart.connector']
    _usage = 'record.importer'
    
    def run(self, external_id, force=False):
        """Run the synchronization job. The specific behavior will be defined in the child classes."""
        raise NotImplementedError


class BatchImporter(AbstractComponent):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    _name = 'ebisumart.batch.importer'
    _inherit = ['base.importer', 'base.ebisumart.connector']
    _usage = 'batch.importer'

    def run(self, filters=None):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters)
        for record_id in record_ids:
            self._import_record(record_id)

    def _import_record(self, external_id):
        """ Import a record directly or delay the import of the record.

        Method to implement in sub-classes.
        """
        raise NotImplementedError
    
class DirectBatchImporter(AbstractComponent):
    """ Import the records directly, without delaying the jobs. """

    _name = 'ebisumart.direct.batch.importer'
    _inherit = 'ebisumart.batch.importer'

    def _import_record(self, external_id):
        """ Import the record directly """
        # add logic here

class DelayedBatchImporter(AbstractComponent):
    """ Delay import of the records """

    _name = 'ebisumart.delayed.batch.importer'
    _inherit = 'ebisumart.batch.importer'

    def _import_record(self, external_id, job_options=None, **kwargs):
        """ Delay the import of the records"""
        # add logic here
