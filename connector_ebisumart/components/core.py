# Copyright 2023 Quartile Limited

from odoo.addons.component.core import AbstractComponent


class BaseEbisumartConnector(AbstractComponent):
    """ Base Ebisumart Connector Component

    All components of this connector should inherit from it.
    """

    _name = 'base.ebisumart.connector'
    _inherit = 'base.connector'
    _collection = 'ebisumart.backend'
