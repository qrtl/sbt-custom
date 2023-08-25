# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo import _


class ResPartnerMapper(Component):
    _name = 'ebisumart.res.partner.import.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = ['ebisumart.res.partner']

    direct = [
        ("TORIHIKISAKI_ID", "ebisumart_id"),
        ("TORIHIKISAKI_NAME", "name"),
    ]
    
    @mapping
    def ref(self, record):
        return {'ref': record['TORIHIKISAKI_CD'] + '_S'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

class ResPartnerBatchImporter(Component):
    _name = 'ebisumart.res.partner.batch.importer'
    _inherit = 'ebisumart.delayed.batch.importer'
    _apply_on = ['ebisumart.res.partner']

    def run(self, filters=None):
        """ Run the synchronization """
        external_datas = self.backend_adapter.search(filters)
        external_ids = [item["TORIHIKISAKI_ID"] for item in external_datas]
        for external_id in external_ids:
            self._import_record(external_id)

class EbisumartResPartnerImporter(Component):
    _name = 'ebisumart.res.parnter.importer'
    _inherit = 'ebisumart.importer'
    _apply_on = 'ebisumart.res.partner'

    # def _get_partner_binding(self, partner_type):
    #     """ Get the binding for a particular partner type """
    #     return self.env['ebisumart.res.partner'].search([
    #         ('external_id', '=', self.external_id),
    #         ('partner_type', '=', partner_type)
    #     ], limit=1)

    # def _run_partner_import(self, force=False):
    #     """ Special handling for importing partners """

    #     map_record = self._map_data()

    #     for partner_type in ['customer', 'supplier']:
    #         # Search for existing binding
    #         binding = self._get_partner_binding(partner_type)
            
    #         if not force and self._is_uptodate(binding):
    #             return _('Already up-to-date.')
    #         # If binding exists, update associated partner
    #         if binding:
    #             partner_vals = self._update_data(map_record)
    #             partner_vals.update({partner_type: True})
    #             binding.odoo_id.write(partner_vals)
    #         else:
    #             # If not, create a new binding and associated partner
    #             partner_vals = self._create_data(map_record)
    #             partner_vals.update({'customer': False})
    #             partner_vals.update({'supplier': False})
    #             partner_vals.update({partner_type: True})
    #             partner = self.env['res.partner'].create(partner_vals)
    #             binding_vals = {
    #                 'odoo_id': partner.id,
    #                 'external_id': self.external_id,
    #                 'partner_type': partner_type,
    #                 'backend_id': self.backend_record.id
    #             }
    #             self.env['ebisumart.res.partner'].create(binding_vals)
    #     self._after_import(binding)

    def _after_import(self, binding):
        binding.odoo_id._after_import()