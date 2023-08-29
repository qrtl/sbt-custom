# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class EbisumartImportMapper(AbstractComponent):
    _name = 'ebisumart.import.mapper'
    _inherit = ['base.ebisumart.connector', 'base.import.mapper']
    _usage = 'import.mapper'

def normalize_datetime(field):
    """Change a invalid date which comes from Ebisumart, if
    no real date is set to null for correct import to
    Odoo"""

    def modifier(self, record, to_attr):
        if record[field] == '0000-00-00 00:00:00':
            return None
        return record[field]
    return modifier
