# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class StockDeliveryReportXlsx(models.TransientModel):
    _name = "report.stock_delivery_report_sbt.stock_delivery_report_xlsx"
    _inherit = [
        "report.report_xlsx_abstract_sbt.abstract_report_xlsx",
        "stock.report.common.mixin",
    ]

    def _get_report_name(self, report):
        return _("Stock Delivery Report")

    def _get_report_columns(self, report):
        return {
            0: {"header": _("Order Number"), "field": "order_number", "width": 20},
            1: {"header": _("Store Code"), "field": "shop_code", "width": 15},
            2: {"header": _("Store Name"), "field": "shop_name", "width": 25},
            3: {"header": _("Payment Method"), "field": "payment_method", "width": 15},
            4: {"header": _("Flag"), "field": "invoice_flag", "width": 5},
            5: {"header": _("Delivery/Return Date"), "field": "date", "width": 15},
            6: {"header": _("Product Code"), "field": "product_code", "width": 25},
            7: {"header": _("Product Name"), "field": "product_name", "width": 25},
            8: {
                "header": _("Supplier Product Code"),
                "field": "supplier_product_code",
                "width": 20,
            },
            9: {
                "header": _("Line No"),
                "field": "line_no",
                "type": "quantity",
                "width": 15,
            },
            10: {
                "header": _("Delivery/Return Qty"),
                "field": "quantity",
                "type": "quantity",
                "width": 20,
            },
            11: {
                "header": _("Delivery/Return Amount"),
                "field": "amount",
                "type": "amount",
                "width": 20,
            },
            12: {
                "header": _("Tax Amount"),
                "field": "tax_amount",
                "type": "amount",
                "width": 15,
            },
            13: {
                "header": _("Delivery/Return Amount (JPY)"),
                "field": "amount_jpy",
                "type": "amount_company",
                "width": 20,
            },
            14: {
                "header": _("Tax Amount (JPY)"),
                "field": "tax_amount_jpy",
                "type": "amount_company",
                "width": 15,
            },
            15: {
                "header": _("Exchange Rate"),
                "field": "exchange_rate",
                "type": "exchange_rate",
                "width": 15,
            },
            16: {"header": _("Invoice Number"), "field": "invoice_number", "width": 15},
            17: {"header": _("Unified number"), "field": "unified_number", "width": 15},
            18: {"header": _("Status"), "field": "status", "width": 10},
        }

    def _get_report_filters(self, report):
        date_from = (
            report.date_from
            and self._convert_filter_date_string(report.date_from)
            or ""
        )
        date_to = (
            report.date_to and self._convert_filter_date_string(report.date_to) or ""
        )
        return [
            [
                report.report_type == "outgoing"
                and _("Delivery Date")
                or _("Return Date"),
                _("%s ~ %s") % (date_from or "", date_to or ""),
            ],
            [
                _("Store Code"),
                ", ".join(
                    [
                        e.ref and e.ref or e.name
                        for e in report.filter_picking_partner_ids
                    ]
                ),
            ],
            [_("Status"), report.state or ""],
        ]

    def _get_col_count_filter_name(self):
        return 1

    def _get_col_count_filter_value(self):
        return 1

    def _generate_report_content(self, workbook, report):
        self.write_array_header()
        data = self._get_sheet_data(report)
        for line in data:
            self.write_line(line)

    def _get_sale_line_ids(self, move_ids):
        query = """
SELECT
    sm.sale_line_id AS sale_line_id
FROM
    stock_move sm
WHERE sm.id IN %s
"""
        params = [tuple(move_ids)]
        self._cr.execute(query, params)
        return [item[0] for item in self._cr.fetchall()]

    def _get_invoice_line_dict(self, report, invoice_type, sale_line_ids):
        query = """
SELECT
    solir.order_line_id AS sale_line_id,
    ai.exchange_rate AS exchange_rate,
    ai.number AS invoice_number,
    ai.state AS status,
    ail.currency_id AS currency_id,
    ail.price_unit AS price_unit,
    ail.price_subtotal AS amount,
    (ail.price_total - ail.price_subtotal) AS tax_amount
FROM
    account_invoice_line ail
JOIN account_invoice ai ON ai.id = ail.invoice_id
JOIN sale_order_line_invoice_rel solir ON solir.invoice_line_id = ail.id
"""

        query += """
WHERE ai.type = %s
AND solir.order_line_id IN %s
AND ai.state <> 'cancel'
"""
        params = [invoice_type, tuple(sale_line_ids)]
        if report.state:
            query += """
AND ai.state = %s
"""
            params.append(report.state)
        self._cr.execute(query, params)
        query_res = self._cr.dictfetchall()
        invoice_line_dict = {}
        for res in query_res:
            invoice_line_vals = self._get_invoice_line_vals(res)
            if res["sale_line_id"] not in invoice_line_dict:
                invoice_line_dict[res["sale_line_id"]] = []
            invoice_line_dict[res["sale_line_id"]].append(invoice_line_vals)
        return invoice_line_dict

    def _get_report_data_rows(self, move_ids):
        query = """
WITH stock_qty_done AS (
    SELECT
        sml.move_id,
        SUM(sml.qty_done) AS quantity
    FROM
        stock_move_line sml
    JOIN stock_move sm ON sm.id = sml.move_id
    JOIN procurement_group pg ON pg.id = sm.group_id
    WHERE sml.state = 'done'
    AND sm.sale_line_id IS NOT NULL
    GROUP BY sml.move_id
)
SELECT
    so.name AS order_number,
    rp.ref AS shop_code,
    rp.name AS shop_name,
    pp.default_code AS product_code,
    pt.name AS product_name,
    pt.id AS product_id,
    sqd.quantity AS quantity,
    sp.scheduled_date AS scheduled_date,
    aj.name AS payment_method,
    so.unified_number AS unified_number,
    so.date_order AS date_order,
    spt.code AS picking_type,
    sm.sale_line_id AS sale_line_id
FROM
    stock_move sm
JOIN stock_picking sp ON sp.id = sm.picking_id
JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
JOIN product_product pp ON pp.id = sm.product_id
JOIN product_template pt ON pt.id = pp.product_tmpl_id
JOIN res_partner rp ON rp.id = sp.partner_id
JOIN sale_order_line sol ON sol.id = sm.sale_line_id
JOIN sale_order so ON so.id = sol.order_id
JOIN stock_qty_done sqd ON sqd.move_id = sm.id
JOIN account_journal aj ON aj.id = so.journal_id
WHERE
    sm.id in %s
ORDER BY
    order_number, move_id
        """
        params = [tuple(move_ids)]
        self._cr.execute(query, params)
        query_res = self._cr.dictfetchall()
        return query_res

    def _get_sheet_data(self, report):
        hours_diff = self._get_tz_hours_diff()
        move_ids = self._get_move_ids(report)
        product_ids = self._get_product_ids(move_ids)
        product_info_dict = self._get_product_info_dict(product_ids)
        sale_line_ids = self._get_sale_line_ids(move_ids)
        customer_invoice_line_dict = self._get_invoice_line_dict(
            report, "out_invoice", sale_line_ids
        )
        customer_refund_line_dict = self._get_invoice_line_dict(
            report, "out_refund", sale_line_ids
        )
        data_rows = self._get_report_data_rows(move_ids)
        result = []
        last_invoice = False
        last_line = 1
        for row in data_rows:
            line = {}
            line["order_number"] = row["order_number"] or ""
            line["shop_code"] = row["shop_code"] or ""
            line["shop_name"] = row["shop_name"] or ""
            line["payment_method"] = row["payment_method"] or ""
            line["invoice_flag"] = "P" if row["picking_type"] == "outgoing" else "R"
            line["date"] = (
                self._convert_to_user_date_string(row["scheduled_date"], hours_diff)
                or ""
            )
            line["product_code"] = row["product_code"] or ""
            line["product_name"] = row["product_name"] or ""
            line["quantity"] = row["quantity"] or 0
            # Since there is not supplier reference, get the first supplier as
            # the product code.
            line["supplier_product_code"] = (
                row["product_id"] in product_info_dict
                and product_info_dict[row["product_id"]]
                and product_info_dict[row["product_id"]][
                    list(product_info_dict[row["product_id"]])[0]
                ]
                or ""
            )
            line["unified_number"] = row["unified_number"] or ""
            line["sort_date"] = row["date_order"] or row["scheduled_date"]
            if row["picking_type"] == "outgoing":
                invoice_lines = (
                    row["sale_line_id"] in customer_invoice_line_dict
                    and customer_invoice_line_dict[row["sale_line_id"]]
                    or False
                )
            else:
                invoice_lines = (
                    row["sale_line_id"] in customer_refund_line_dict
                    and customer_refund_line_dict[row["sale_line_id"]]
                    or False
                )
            if report.state and not invoice_lines:
                continue
            # Single invoice line case
            if len(invoice_lines) == 1:
                invoice_line = invoice_lines[0]
                line["amount"] = invoice_line["amount"] or 0
                line["tax_amount"] = invoice_line["tax_amount"] or 0
                line["amount_jpy"] = invoice_line["amount_jpy"] or 0
                line["tax_amount_jpy"] = invoice_line["tax_amount_jpy"] or 0
                line["exchange_rate"] = invoice_line["exchange_rate"] or 0
                line["invoice_number"] = invoice_line["invoice_number"] or ""
                line["status"] = invoice_line["status"]
            # Multiple invoice lines case, price_unit and status will only be
            # assigned when all invoice lines have the same value on them.
            elif len(invoice_lines) > 1:
                line["status"] = "N/A"
                line["amount"] = 0
                line["tax_amount"] = 0
                line["amount_jpy"] = 0
                line["tax_amount_jpy"] = 0
                line["exchange_rate"] = 0
                status_list = []
                exchange_rate_list = []
                invoice_number_list = []
                for invoice_line in invoice_lines:
                    invoice_number_list.append(invoice_line["invoice_number"] or "")
                    status_list.append(invoice_line["status"])
                    exchange_rate_list.append(invoice_line["exchange_rate"])
                    line["amount"] += invoice_line["amount"]
                    line["tax_amount"] += invoice_line["tax_amount"]
                    line["amount_jpy"] += invoice_line["amount_jpy"]
                    line["tax_amount_jpy"] += invoice_line["tax_amount_jpy"]
                if len(set(status_list)) == 1:
                    line["status"] = status_list[0]
                if len(set(exchange_rate_list)) == 1:
                    line["exchange_rate"] = exchange_rate_list[0]
                line["invoice_number"] = ",".join(invoice_number_list)
            # Calculate the line no, increment from the last line_no in
            # case the current row has the same invoice number as the last
            # record.
            if line["invoice_number"] and last_invoice == line["invoice_number"]:
                line["line_no"] = last_line = last_line + 1
            else:
                line["line_no"] = last_line = 1
            last_invoice = line["invoice_number"]
            result.append(line)
        result.sort(key=lambda x: x["sort_date"])
        return result
