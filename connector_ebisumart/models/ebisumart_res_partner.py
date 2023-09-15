# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.component.core import Component


class EbisumartResPartner(models.Model):
    _name = 'ebisumart.res.partner'
    _inherit = 'ebisumart.binding'
    _inherits = {'res.partner': 'odoo_id'}
    _description = 'Ebisumart Partner'

    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade'
    )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ebisumart_bind_ids = fields.One2many(
        comodel_name='ebisumart.res.partner',
        inverse_name='odoo_id',
        string='Ebisumart Bindings'
    )


class ResPartnerAdapter(Component):
    _name = 'ebisumart.res.parnter.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.res.partner']

    # Add methods for communicating with the Ebisumart API
    def search(self, attributes=None, filters=None):
        # Call the base method with the "/suppliers" endpoint
        attributes = ['TORIHIKISAKI_ID']
        return super().search("/suppliers", attributes=attributes, filters=filters)

    def read(self, external_id, attributes=None):
        """ Returns the detailed information for an existing product."""
        # Adjust the URL endpoint accordingly
        if not attributes:
            attributes = ['TORIHIKISAKI_ID', 'TORIHIKISAKI_CD', 'TORIHIKISAKI_NAME']
        return super().read(f"/suppliers/{external_id}", attributes=attributes)
