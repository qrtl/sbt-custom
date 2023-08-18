# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from ..components.mapper import normalize_datetime
from odoo import fields


class PurchaseOrderImportMapper(Component):
    _name = 'ebisumart.purchase.order.import.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = ['ebisumart.purchase.order']

    direct = [
        ("ORDER_NO", "external_id"),
        ("ORDER_DISP_NO", "name"),
        (normalize_datetime('SEND_DATE'), 'date_order'),
        (normalize_datetime('REGIST_DATE'), 'created_at'),
        (normalize_datetime('UPDATE_DATE'), 'updated_at'),
    ]
    children = [('order_details', 'ebisumart_order_line_ids', 'ebisumart.purchase.order.line')]

    @mapping
    def partner_id(self, record):
        for line in record.get('order_details', []):
            binder = self.binder_for('ebisumart.product.product')
            product = binder.to_internal(line['ITEM_ID'], unwrap=True)
            if product and product.torihikisaki_id != 0:
                partner = self.env["res.partner"].search([('ebisumart_id','=', product.torihikisaki_id),('supplier','=',True)],limit=1)
                sales_partner = self.env["res.partner"].search([('ebisumart_id','=', product.torihikisaki_id),('customer','=',True)],limit=1)
                partner.write({'sales_partner': sales_partner.id})
                if partner:
                    return {'partner_id': partner.id}
        return {}
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

class PurchaseOrderLineMapper(Component):
    _name = 'ebisumart.purchase.order.line.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = 'ebisumart.purchase.order.line'

    direct = [('ORDER_D_NO', 'external_id'),
              ('ITEM_NAME', 'name'),
              ('SHIRE_PRICE', 'price_unit'),
              ('QUANTITY', 'product_qty')]
    
    @mapping
    def product(self, record):
        binder = self.binder_for('ebisumart.product.product')
        product = binder.to_internal(record['ITEM_ID'], unwrap=True)
        assert product, (
            "product_id %s should have been imported in "
            "PurchaseOrderImporter._import_dependencies" % record['ITEM_ID'])
        return {'product_id': product.id, 'product_uom': product.uom_id.id}


class PurchaseOrderBatchImporter(Component):
    _name = 'ebisumart.purchase.order.batch.importer'
    _inherit = 'ebisumart.delayed.batch.importer'
    _apply_on = ['ebisumart.purchase.order']

    def run(self, filters=None):
        """ Run the synchronization """
        external_datas = self.backend_adapter.search(filters)
        external_ids = [
            order["ORDER_NO"]
            for order in external_datas
            if order.get('ORDER_DISP_NO') and
            order.get('AUTHORY_DATE') and
            order.get('SEND_DATE') and 
            not order.get('CANCEL_DATE')
        ]
        for external_id in external_ids:
            self._import_record(external_id)

class EbisumartPurchaseOrderImporter(Component):
    _name = 'ebisumart.purchase.order.importer'
    _inherit = 'ebisumart.importer'
    _apply_on = 'ebisumart.purchase.order'

    def _import_dependencies(self):
        record = self.ebisumart_record
        for line in record.get('order_details', []):
            self._import_dependency(line['ITEM_ID'], 'ebisumart.product.product')
