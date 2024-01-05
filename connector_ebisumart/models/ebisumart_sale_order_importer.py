# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from ..components.mapper import normalize_datetime


class SaleOrderImportMapper(Component):
    _name = 'ebisumart.sale.order.import.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = ['ebisumart.sale.order']

    direct = [
        ("ORDER_NO", "external_id"),
        ("ORDER_DISP_NO", "name"),
        (normalize_datetime('SEND_DATE'), 'ebisumart_send_date'),
        (normalize_datetime('CANCEL_DATE'), 'ebisumart_cancel_date'),
        (normalize_datetime('REGIST_DATE'), 'created_at'),
        (normalize_datetime('UPDATE_DATE'), 'updated_at'),
    ]
    children = [
        ('order_details', 'ebisumart_order_line_ids', 'ebisumart.sale.order.line')
    ]

    @mapping
    def partner_id(self, record):
        for line in record.get('order_details', []):
            binder = self.binder_for('ebisumart.product.product')
            product = binder.to_internal(line['ITEM_ID'], unwrap=True)
            if product and product.torihikisaki_id != 0:
                vendor = self.env["res.partner"].search(
                    [
                        ('ebisumart_id', '=', product.torihikisaki_id),
                        ('supplier', '=', True)
                    ], limit=1)

                existing_supplierinfo = self.env['product.supplierinfo'].search([
                    ('name', '=', vendor.id),
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('price', '=', line['SHIRE_PRICE'])
                ])
                # If no existing supplierinfo with the same price, supplier and product
                if not existing_supplierinfo:
                    self.env['product.supplierinfo'].create({
                        'name': vendor.id,
                        'price': line['SHIRE_PRICE'],
                        'product_tmpl_id': product.product_tmpl_id.id,
                    })
        return {'partner_id': self.backend_record.sale_partner_id.id}

    @mapping
    def journal_id(self, record):
        if record['KESSAI_ID'] == 61:
            journal = self.env["account.journal"].search(
                [("ebisumart_payment_type", "=", "credit_card")], limit=1
            )
            if journal:
                return {'journal_id': journal.id}
        else:
            journal = self.env["account.journal"].search(
                [("ebisumart_payment_type", "=", "payment_slip")], limit=1
            )
            if journal:
                return {'journal_id': journal.id}
        return

    @mapping
    def workflow_process_id(self, record):
        workflow_process_id = self.env["sale.workflow.process"].search(
            [("name", "=", "Ebisumart Sale Automatic")], limit=1
        )
        return {'workflow_process_id': workflow_process_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def cancel_in_ebisumart(self, record):
        if record.get('CANCEL_DATE'):
            return {'cancel_in_ebisumart': True}
        return {'cancel_in_ebisumart': False}


class SaleOrderLineMapper(Component):
    _name = 'ebisumart.sale.order.line.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = 'ebisumart.sale.order.line'

    direct = [('ORDER_D_NO', 'external_id'),
              ('ITEM_NAME', 'name'),
              ('TEIKA', 'price_unit'),
              ('QUANTITY', 'product_uom_qty')]

    @mapping
    def product(self, record):
        binder = self.binder_for('ebisumart.product.product')
        product = binder.to_internal(record['ITEM_ID'], unwrap=True)
        assert product, (
            "product_id %s should have been imported in "
            "SaleOrderImporter._import_dependencies" % record['ITEM_ID'])
        return {'product_id': product.id, 'product_uom': product.uom_id.id}


class SaleOrderBatchImporter(Component):
    _name = 'ebisumart.sale.order.batch.importer'
    _inherit = 'ebisumart.delayed.batch.importer'
    _apply_on = ['ebisumart.sale.order']

    def run(self, filters=None):
        """ Run the synchronization """
        external_datas = self.backend_adapter.search(filters)
        external_ids = [
            order["ORDER_NO"]
            for order in external_datas
            if order.get('ORDER_DISP_NO')
            and order.get('SEND_DATE')
            and order.get('FREE_ITEM1')
            and not order.get('IS_TEIKI_HEADER_FLG')
        ]

        for external_id in external_ids:
            self._import_record(external_id)


class EbisumartSaleOrderImporter(Component):
    _name = 'ebisumart.sale.order.importer'
    _inherit = 'ebisumart.importer'
    _apply_on = 'ebisumart.sale.order'

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        if self.binder.to_internal(self.external_id):
            return _('Already imported')

    def _import_dependencies(self):
        record = self.ebisumart_record
        for line in record.get('order_details', []):
            self._import_dependency(line['ITEM_ID'], 'ebisumart.product.product')

    def _after_import(self, binding):
        binding.odoo_id.after_import(self.ebisumart_record, self.backend_record)
