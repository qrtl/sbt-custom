# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.exception import NothingToDoJob

_logger = logging.getLogger(__name__)


class EbisumartImporter(AbstractComponent):
    _name = 'ebisumart.importer'
    _inherit = ['base.importer', 'base.ebisumart.connector']
    _usage = 'record.importer'

    def __init__(self, work_context):
        super(EbisumartImporter, self).__init__(work_context)
        self.external_id = None
        self.ebisumart_record = None

    def _get_ebisumart_data(self):
        """ Return the raw Ebisumart data for ``self.external_id`` """
        return self.backend_adapter.read(self.external_id)

    def _validate_data(self, data):
        """ Check if the values to import are correct
        """
        return

    def _create_data(self, map_record, fields=None, **kwargs):
        """ Get the data to pass to :py:meth:`_create` """
        return map_record.values(for_create=True, fields=fields, **kwargs)

    def _create(self, data):
        """ Create the Odoo record """
        # special check on data before import
        self._validate_data(data)
        model = self.model.with_context(connector_no_export=True)
        binding = model.create(data)
        _logger.debug('%d created from ebisumart %s', binding, self.external_id)
        return binding

    def _get_binding(self):
        return self.binder.to_internal(self.external_id)

    def _is_uptodate(self, binding):
        """Return True if the import should be skipped because
        it is already up-to-date in Odoo"""
        assert self.ebisumart_record
        if not self.ebisumart_record.get('UPDATE_DATE'):
            return  # no update date on Ebisumart, always import it.
        if not binding:
            return  # it does not exist so it should not be skipped
        sync = binding.sync_date
        if not sync:
            return
        from_string = fields.Datetime.from_string
        sync_date = from_string(sync)
        ebisumart_date = from_string(self.ebisumart_record['UPDATE_DATE']) # To Replace updated_at
        return ebisumart_date < sync_date

    def _import_dependency(self, external_id, binding_model,
                           importer=None, always=False):
        if not external_id:
            return
        binder = self.binder_for(binding_model)
        if always or not binder.to_internal(external_id):
            if importer is None:
                importer = self.component(usage='record.importer',
                                          model_name=binding_model)
            try:
                importer.run(external_id)
            except NothingToDoJob:
                _logger.info(
                    'Dependency import of %s(%s) has been ignored.',
                    binding_model._name, external_id
                )


    def _import_dependencies(self):
        """ Import the dependencies for the record

        Import of dependencies can be done manually or by calling
        :meth:`_import_dependency` for each dependency.
        """
        return

    def _map_data(self):
        return self.mapper.map_record(self.ebisumart_record)

    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        """ Update an Odoo record """
        # special check on data before import
        self._validate_data(data)
        binding.with_context(connector_no_export=True).write(data)
        _logger.debug('%d updated from ebisumart %s', binding, self.external_id)
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    def run(self, external_id, force=False, data=None):
        """ Run the synchronization

        :param external_id: identifier of the record on Ebisumart
        """
        self.external_id = external_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.work.model_name,
            external_id,
        )
        if data:
            self.ebisumart_record = data
        else:
            try:
                self.ebisumart_record = self._get_ebisumart_data()
            except IDMissingInBackend:
                return _('Record does no longer exist in Ebisumart')

        binding = self._get_binding()

        if not force and self._is_uptodate(binding):
            return _('Already up-to-date.')

        # Keep a lock on this import until the transaction is committed
        # The lock is kept since we have detected that the informations
        # will be updated into Odoo
        self.advisory_lock_or_retry(lock_name)

        # import the missing linked resources
        self._import_dependencies()

        map_record = self._map_data()

        if binding:
            record = self._update_data(map_record)
            self._update(binding, record)
        else:
            record = self._create_data(map_record)
            binding = self._create(record)

        self.binder.bind(self.external_id, binding)
        self._after_import(binding)

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
        self.model.import_record(self.backend_record, external_id)

class DelayedBatchImporter(AbstractComponent):
    """ Delay import of the records """

    _name = 'ebisumart.delayed.batch.importer'
    _inherit = 'ebisumart.batch.importer'

    def _import_record(self, external_id, job_options=None, **kwargs):
        """ Delay the import of the records"""
        delayable = self.model.with_delay(**job_options or {})
        delayable.import_record(self.backend_record, external_id, **kwargs)
