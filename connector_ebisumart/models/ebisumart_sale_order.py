# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.component.core import Component


class EbisumartSaleOrder(models.Model):
    _name = 'ebisumart.sale.order'
    _inherit = 'ebisumart.binding'
    _inherits = {'sale.order': 'odoo_id'}
    _description = 'Ebisumart Sale Order'

    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade'
    )
    ebisumart_order_line_ids = fields.One2many(
        comodel_name='ebisumart.sale.order.line',
        inverse_name='ebisumart_order_id',
        string='Ebisumart Order Lines'
    )
    created_at = fields.Date('Created At (on Ebisumart)')
    updated_at = fields.Date('Updated At (on Ebisumart)')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ebisumart_bind_ids = fields.One2many(
        comodel_name='ebisumart.sale.order',
        inverse_name='odoo_id',
        string='Ebisumart Bindings'
    )
    cancel_in_ebisumart = fields.Boolean()
    ebisumart_send_date = fields.Datetime()
    ebisumart_cancel_date = fields.Datetime()

    def get_tax_exclusive_price(self, price_inclusive, tax_percent):
        """
        Calculates the tax-exclusive price given a tax-inclusive price and tax rate.
        """
        return price_inclusive / (1 + tax_percent / 100.0)

    def after_import(self, ebisumart_record, backend_record):
        if (ebisumart_record.get('COUPON_WARIBIKI')
                and ebisumart_record['COUPON_WARIBIKI'] > 0):
            taxes = backend_record.coupon_product_id.taxes_id
            total_tax_percent = sum(tax.amount for tax in taxes)
            price_unit_exclusive = self.get_tax_exclusive_price(
                ebisumart_record['COUPON_WARIBIKI'], total_tax_percent
            )
            self.env['sale.order.line'].create({
                'product_id': backend_record.coupon_product_id.id,
                'price_unit': -1 * price_unit_exclusive,
                'product_uom': backend_record.coupon_product_id.uom_id.id,
                'product_uom_qty': 1.0,
                'order_id': self.id,
                'name': backend_record.coupon_product_id.name,
            })
        self.action_confirm()
        # Search purchase order
        po = self.env['purchase.order'].search([('origin', '=', self.name)])
        if not po:
            return
        # map data_planned
        for line in po.order_line:
            line.date_planned = po.date_order
        # Confirm the purchase order.
        po.button_confirm()
        # Validate the associated receipt (stock picking).
        for picking in po.picking_ids:
            wiz = self.env['stock.immediate.transfer'].create(
                {'pick_ids': [(4, picking.id)]}
            )
            wiz.process()

        po_invoice = {
            'partner_id': po.partner_id.id,
            'account_id': po.partner_id.property_account_payable_id.id,
            'state': 'draft',
            'type': 'in_invoice',
            'purchase_id': po.id,
        }
        inv = self.env['account.invoice'].create(po_invoice)
        inv.purchase_order_change()
        # Recalculate the invoice lines.
        inv._onchange_invoice_line_ids()
        inv.action_invoice_open()
        # Force assign scheduled_date
        # TODO put this line after action_confirm()
        self.picking_ids.write({'scheduled_date': self.ebisumart_send_date})


class EbisumartSaleOrderLine(models.Model):
    _name = 'ebisumart.sale.order.line'
    _inherit = 'ebisumart.binding'
    _description = 'Ebisumart Sale Order Line'
    _inherits = {'sale.order.line': 'odoo_id'}

    ebisumart_order_id = fields.Many2one(
        comodel_name='ebisumart.sale.order',
        string='Ebisumart Sale Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order Line',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        related='ebisumart_order_id.backend_id',
        string='Ebisumart Backend',
        readonly=True,
        store=True,
        required=False
    )

    @api.model
    def create(self, vals):
        ebisumart_order_id = vals['ebisumart_order_id']
        binding = self.env['ebisumart.sale.order'].browse(ebisumart_order_id)
        vals['order_id'] = binding.odoo_id.id
        binding = super().create(vals)
        return binding


class SaleOrderAdapter(Component):
    _name = 'ebisumart.sale.order.adapter'
    _inherit = ['ebisumart.adapter']
    _apply_on = ['ebisumart.sale.order']

    def search(self, attributes=None, filters=None):
        last_fetch_date = self.backend_record.last_fetch_order_date
        if last_fetch_date:
            filters = self._get_date_filters(last_fetch_date)
        self.backend_record.last_fetch_order_date = fields.datetime.now()
        attributes = [
            'ORDER_NO', 'KESSAI_ID', 'ORDER_DISP_NO',
            'SEND_DATE', 'CANCEL_DATE', 'FREE_ITEM1', 'IS_TEIKI_HEADER_FLG',
        ]
        return super().search("/orders", attributes=attributes, filters=filters)

    def read(self, external_id, attributes=None):
        if not attributes:
            attributes = [
                'ORDER_NO', 'KESSAI_ID', 'ORDER_DISP_NO', 'SEND_DATE',
                'order_details(ORDER_D_NO, ITEM_ID, ITEM_NAME, QUANTITY, '
                'TEIKA, SHIRE_PRICE)',
                'REGIST_DATE', 'UPDATE_DATE', 'COUPON_WARIBIKI', 'CANCEL_DATE',
            ]
        return super().read(f"/orders/{external_id}", attributes=attributes)
