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

    def create_return_receipt(self, purchase_order):
        for receipt in purchase_order.picking_ids.filtered(lambda r: r.state == 'done'):
            # Create the reverse transfer (return receipt)
            stock_return_picking = self.env['stock.return.picking']
            return_wizard = stock_return_picking.with_context(active_ids=receipt.ids, active_id=receipt.ids[0]).create({})
            return_wizard.create_returns()
        
    def create_vendor_credit_note(self, purchase_order):
        for invoice in purchase_order.invoice_ids.filtered(lambda r: r.state not in ['cancel','draft'] and r.type == 'in_invoice'):
            # Create the refund (vendor credit note)
            account_invoice_refund = self.env['account.invoice.refund']
            refund_wizard = account_invoice_refund.create({
                'description': 'Credit Note',
                'filter_refund': 'refund',  # refund the entire invoice
            })
            refund_wizard.with_context(active_ids=invoice.ids).invoice_refund()

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
        cancel_ids = [
            order["ORDER_NO"]
            for order in external_datas
            if order.get('CANCEL_DATE')
        ]
        for external_id in cancel_ids:
            binder = self.binder_for('ebisumart.purchase.order')
            purchase_order = binder.to_internal(external_id, unwrap=True)
            if purchase_order:
                if purchase_order.cancel_in_ebisumart:
                    continue
                self.create_return_receipt(purchase_order)
                self.create_vendor_credit_note(purchase_order)
                purchase_order.write({"cancel_in_ebisumart": True})
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

    def _after_import(self, binding):
        binding.odoo_id._after_import()
