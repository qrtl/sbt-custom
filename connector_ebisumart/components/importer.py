# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from contextlib import closing, contextmanager
from datetime import datetime

import odoo
from odoo import _, fields, tools

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.exception import NothingToDoJob, RetryableJobError

import pytz

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

    def convert_ebisumart_date_to_utc(self, raw_date):
        """
        Convert an Ebisumart date (assumed to be in user's timezone)
        to offset-naive UTC datetime object.
        """
        # If the date is invalid, return None
        if raw_date == '0000-00-00 00:00:00':
            return None

        # Handle datetime strings that might have milliseconds
        try:
            naive_dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            naive_dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")

        # Assume the naive datetime is in the user's timezone
        user_timezone = pytz.timezone(self.env.user.tz)
        aware_dt = user_timezone.localize(naive_dt)

        # Convert the timezone-aware datetime to UTC
        utc_dt = aware_dt.astimezone(pytz.UTC)

        # Return offset-naive UTC datetime
        return utc_dt.replace(tzinfo=None)

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
        ebisumart_date = self.convert_ebisumart_date_to_utc(
            self.ebisumart_record['UPDATE_DATE']
        )
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

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    @contextmanager
    def do_in_new_work_context(self, model_name=None):
        """ Context manager that yields a new component work context

        Using a new Odoo Environment thus a new PG transaction.

        This can be used to make a preemptive check in a new transaction,
        for instance to see if another transaction already made the work.
        """
        with odoo.api.Environment.manage():
            registry = odoo.registry(self.env.cr.dbname)
            with closing(registry.cursor()) as cr:
                try:
                    new_env = odoo.api.Environment(cr, self.env.uid,
                                                   self.env.context)
                    backend = self.backend_record.with_env(new_env)
                    with backend.work_on(model_name
                                         or self.model._name) as work:
                        yield work
                except Exception:
                    cr.rollback()
                    raise
                else:
                    if not tools.config['test_enable']:
                        cr.commit()  # pylint: disable=invalid-commit

    def run(self, external_id, force=False, data=None):
        """ Run the synchronization

        :param external_id: identifier of the record on Ebisumart
        """
        self.external_id = external_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            external_id,
        )
        if data:
            self.ebisumart_record = data
        else:
            try:
                self.ebisumart_record = self._get_ebisumart_data()
            except IDMissingInBackend:
                return _('Record does no longer exist in Ebisumart')

        skip = self._must_skip()    # pylint: disable=assignment-from-none
        if skip:
            return skip

        binding = self._get_binding()
        if not binding:
            with self.do_in_new_work_context() as new_work:
                # Even when we use an advisory lock, we may have
                # concurrent issues.
                # Explanation:
                # We import Partner A and B, both of them import a
                # partner category X.
                #
                # The squares represent the duration of the advisory
                # lock, the transactions starts and ends on the
                # beginnings and endings of the 'Import Partner'
                # blocks.
                # T1 and T2 are the transactions.
                #
                # ---Time--->
                # > T1 /------------------------\
                # > T1 | Import Partner A       |
                # > T1 \------------------------/
                # > T1        /-----------------\
                # > T1        | Imp. Category X |
                # > T1        \-----------------/
                #                     > T2 /------------------------\
                #                     > T2 | Import Partner B       |
                #                     > T2 \------------------------/
                #                     > T2        /-----------------\
                #                     > T2        | Imp. Category X |
                #                     > T2        \-----------------/
                #
                # As you can see, the locks for Category X do not
                # overlap, and the transaction T2 starts before the
                # commit of T1. So no lock prevents T2 to import the
                # category X and T2 does not see that T1 already
                # imported it.
                #
                # The workaround is to open a new DB transaction at the
                # beginning of each import (e.g. at the beginning of
                # "Imp. Category X") and to check if the record has been
                # imported meanwhile. If it has been imported, we raise
                # a Retryable error so T2 is rollbacked and retried
                # later (and the new T3 will be aware of the category X
                # from the its inception).
                binder = new_work.component(usage='binder')
                if binder.to_internal(self.external_id):
                    raise RetryableJobError(
                        'Concurrent error. The job will be retried later',
                        seconds=1,
                        ignore_retry=True
                    )

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
