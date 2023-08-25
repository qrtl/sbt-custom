# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EbisumarttoModelBinder(Component):
    """ Bind records and give odoo/ebisumart ids correspondence

    Binding models are models called ``ebisumart.{normal_model}``,
    like ``ebisumart.product.product``.
    They are ``_inherits`` of the normal models and contains
    the ebisumart ID, the ID of the ebisumart Backend and the additional
    fields belonging to the ebisumart instance.
    """
    _name = 'ebisumart.binder'
    _inherit = ['base.binder', 'base.ebisumart.connector']
    _apply_on = [
        'ebisumart.product.product',
        'ebisumart.purchase.order',
        'ebisumart.purchase.order.line',
        'ebisumart.sale.order',
        'ebisumart.sale.order.line',
        'ebisumart.res.partner',
    ]
