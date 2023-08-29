# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ResPartnerMapper(Component):
    _name = 'ebisumart.res.partner.import.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = ['ebisumart.res.partner']

    direct = [
        ("TORIHIKISAKI_ID", "ebisumart_id"),
        ("TORIHIKISAKI_NAME", "name"),
    ]

    @mapping
    def company_type(self, record):
        return {'company_type': 'company'}

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

    def _after_import(self, binding):
        binding.odoo_id._after_import()
