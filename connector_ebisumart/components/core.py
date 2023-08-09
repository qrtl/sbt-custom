# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class BaseEbisumartConnector(AbstractComponent):
    """ Base Ebisumart Connector Component

    All components of this connector should inherit from it.
    """

    _name = 'base.ebisumart.connector'
    _inherit = 'base.connector'
    _collection = 'ebisumart.backend'
