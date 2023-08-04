# Copyright 2023 Quartile Limited

from odoo import models, fields, api
from odoo.addons.queue_job.job import job


class EbisumartBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All the models used as bindings between Ebisumart and Odoo
    (``ebisumart.res.partner``, ``ebisumart.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'ebisumart.binding'
    _inherit = 'external.binding'
    _description = 'Ebisumart Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='ebisumart.backend',
        string='Ebisumart Backend',
        required=True,
        ondelete='restrict',
    )

    # The id from the Ebisumart
    external_id = fields.Char(string='ID on Ebisumart', index=True)
    # Add a field to mark when a record was last updated on Ebisumart
    external_last_update = fields.Datetime(string='Last Updated on Ebisumart')

    @job(default_channel='root.ebisumart')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Ebisumart """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.ebisumart')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a Ebisumart record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)