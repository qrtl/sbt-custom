# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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

    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified in Ebisumart.
        This will create a queue job to fetch the list of modified records
        from Ebisumart, and subsequently prepare individual queue jobs for
        each record to be imported.
        """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @api.model
    def import_record(self, backend, external_id, force=False):
        """Import an Ebisumart record.
        This will import the Ebisumart record into Odoo when its queue job is run.
        """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)
