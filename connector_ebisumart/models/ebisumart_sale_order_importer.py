# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo import _

from ..components.mapper import normalize_datetime


class SaleOrderImportMapper(Component):
    _name = 'ebisumart.sale.order.import.mapper'
    _inherit = 'ebisumart.import.mapper'
    _apply_on = ['ebisumart.sale.order']

    direct = [
        ("ORDER_NO", "external_id"),
        ("ORDER_DISP_NO", "name"),
        (normalize_datetime('SEND_DATE'), 'ebisumart_send_date'),
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

    # TODO
    # To search process id with some identifier, not name
    @mapping
    def workflow_process_id(self, record):
        workflow_process_id = self.env["sale.workflow.process"].search(
            [("name", "=", "Ebisumart Sale Automatic")], limit=1
        )
        return {'workflow_process_id': workflow_process_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


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

    
    def create_return_picking(self, order):
        for picking in order.picking_ids.filtered(lambda r: r.state == 'done'):
            # Create the reverse transfer
            stock_return_picking = self.env['stock.return.picking']
            return_wizard = stock_return_picking.with_context(
                active_ids=picking.ids, active_id=picking.ids[0]
            ).create({})
            return_result = return_wizard.create_returns()

            # Usually, the return_result contains information
            # about the newly created return picking(s)
            if return_result and 'res_id' in return_result:
                new_return_picking = self.env['stock.picking'].browse(
                    return_result['res_id']
                )

                # Validate (confirm) the return picking
                if new_return_picking.state != 'done':
                    wiz = self.env['stock.immediate.transfer'].create({
                        'pick_ids': [(4, new_return_picking.id)]
                    })
                    wiz.process()

    def create_credit_note(self, order, invoice_type):
        for invoice in order.invoice_ids.filtered(lambda r: r.state not in ['cancel','draft'] and r.type == invoice_type):
            # Create the refund (credit note)
            account_invoice_refund = self.env['account.invoice.refund']
            refund_wizard = account_invoice_refund.create({
                'description': 'Credit Note',
                'filter_refund': 'refund',  # refund the entire invoice
            })
            refund_result = refund_wizard.with_context(active_ids=invoice.ids).invoice_refund()
            if refund_result and refund_result.get('domain'):
                # Search for the newly created credit note
                credit_notes = self.env['account.invoice'].search(refund_result.get('domain'))
                for credit_note in credit_notes:
                    if credit_note.state == 'draft':
                        credit_note.action_invoice_open()

    def run(self, filters=None):
        """ Run the synchronization """
        external_datas = self.backend_adapter.search(filters)
        external_ids = [
            order["ORDER_NO"]
            for order in external_datas
            if order.get('ORDER_DISP_NO')
            and order.get('SEND_DATE')
            and order.get('FREE_ITEM1')
            and not order.get('CANCEL_DATE')
        ]
        cancel_ids = [
            order["ORDER_NO"]
            for order in external_datas
            if order.get('CANCEL_DATE')
        ]
        for external_id in cancel_ids:
            binder = self.binder_for('ebisumart.sale.order')
            sale_order = binder.to_internal(external_id, unwrap=True)
            if sale_order:
                if sale_order.cancel_in_ebisumart:
                    continue
                self.create_return_picking(sale_order)
                self.create_credit_note(sale_order, invoice_type="out_invoice")
                purchase_order = self.env['purchase.order'].search([('origin', '=', sale_order.name)])
                if purchase_order:
                    self.create_return_picking(purchase_order)
                    self.create_credit_note(purchase_order, invoice_type="in_invoice")
                sale_order.write({"cancel_in_ebisumart": True})

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

