# Copyright 2023 Quartile Limited

from odoo.addons.component.core import AbstractComponent


class EbisumartImportMapper(AbstractComponent):
    _name = 'ebisumart.import.mapper'
    _inherit = ['base.ebisumart.connector', 'base.import.mapper']
    _usage = 'import.mapper'

def normalize_datetime(field):
    """Change a invalid date which comes from ebisumart, if
    no real date is set to null for correct import to
    Odoo"""
    