# Copyright 2023 Quartile Limited

from odoo import models, fields

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
