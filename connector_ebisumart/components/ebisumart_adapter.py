# Copyright 2023 Quartile Limited

from odoo.addons.component.core import AbstractComponent


class EbisumartCRUDAdapter(AbstractComponent):
    _name = 'ebisumart.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.ebisumart.connector']
    _usage = 'backend.adapter'

    def search(self, filters=None):
        """ Search records according to some filters """
        raise NotImplementedError

    def read(self, external_id, fields=None):
        """ Returns the detailed information for record """
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, external_id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, external_id):
        """ Delete a record on the external system """
        raise NotImplementedError

class EbisumartAdapater(AbstractComponent):
    _name = "ebisumart.adapater"
    _inherit = "ebisumart.crud.adapter"

    