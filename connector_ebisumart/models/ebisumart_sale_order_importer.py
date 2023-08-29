# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
                partner = self.env["res.partner"].search(
                    [
                        ('ebisumart_id', '=', product.torihikisaki_id),
                        ('customer', '=', True)
                    ], limit=1)
                return {'partner_id': partner.id}

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

    def create_return_delivery(self, sale_order):
        for delivery in sale_order.picking_ids.filtered(lambda r: r.state == 'done'):
            # Create the reverse transfer (return delivery)
            stock_return_picking = self.env['stock.return.picking']
            return_wizard = stock_return_picking.with_context(
                active_ids=delivery.ids, active_id=delivery.ids[0]
            ).create({})
            # Update the product_return_moves lines to set the is_refund field
            for return_move in return_wizard.product_return_moves:
                return_move.to_refund = True
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

    def run(self, filters=None):
        """ Run the synchronization """
        external_datas = self.backend_adapter.search(filters)
        external_ids = [
            order["ORDER_NO"]
            for order in external_datas
            if order.get('ORDER_DISP_NO')
            and order.get('AUTHORY_DATE')
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
                self.create_return_delivery(sale_order)
                sale_order.write({"cancel_in_ebisumart": True})

        for external_id in external_ids:
            self._import_record(external_id)


class EbisumartSaleOrderImporter(Component):
    _name = 'ebisumart.sale.order.importer'
    _inherit = 'ebisumart.importer'
    _apply_on = 'ebisumart.sale.order'

    def _import_dependencies(self):
        record = self.ebisumart_record
        for line in record.get('order_details', []):
            self._import_dependency(line['ITEM_ID'], 'ebisumart.product.product')
