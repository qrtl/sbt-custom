# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from odoo import _, models


class AccountPaymentReportXlsx(models.TransientModel):
    _name = "report.account_payment_report_sbt.account_payment_report_xlsx"
    _inherit = "report.report_xlsx_abstract_sbt.abstract_report_xlsx"

    def _get_report_name(self, report):
        return _("Account Payment Report")

    def _get_report_columns(self, report):
        return {
            0: {"header": _("Order Number"), "field": "order_number", "width": 20},
            1: {"header": _("Store Code"), "field": "shop_code", "width": 15},
            2: {"header": _("Store Name"), "field": "shop_name", "width": 20},
            3: {"header": _("Payment Method"), "field": "payment_method", "width": 10},
            4: {
                "header": _("Journal Company"),
                "field": "journal_company_name",
                "width": 20,
            },
            5: {"header": _("Flag"), "field": "payment_flag", "width": 5},
            6: {"header": _("Invoice Number"), "field": "invoice_number", "width": 20},
            7: {"header": _("Invoice Date"), "field": "invoice_date", "width": 11},
            8: {
                "header": _("Invoice Amount"),
                "field": "invoice_amount",
                "type": "amount",
                "width": 15,
            },
            9: {
                "header": _("Invoice Amount (JPY)"),
                "field": "invoice_amount_jpy",
                "type": "amount_company",
                "width": 15,
            },
            10: {
                "header": _("Payment/Refund Date"),
                "field": "payment_date",
                "width": 11,
            },
            11: {
                "header": _("Payment/Refund Amount"),
                "field": "payment_amount",
                "type": "amount",
                "width": 15,
            },
            12: {
                "header": _("Payment/Refund Amount (JPY)"),
                "field": "payment_amount_jpy",
                "type": "amount_company",
                "width": 15,
            },
            13: {
                "header": _("Payment/Refund Exchange Rate"),
                "field": "payment_exchange_rate",
                "type": "exchange_rate",
                "width": 20,
            },
            14: {"header": _("MID"), "field": "mid", "width": 5},
            15: {
                "header": _("Residual"),
                "field": "residual",
                "type": "amount",
                "width": 10,
            },
            16: {
                "header": _("Residual (JPY)"),
                "field": "residual_jpy",
                "type": "amount_company",
                "width": 10,
            },
            17: {"header": _("Status"), "field": "status", "width": 10},
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
                report.report_type == "outbound"
                and _("Refund Date")
                or _("Payment Date"),
                _("%s ~ %s") % (date_from, date_to),
            ],
            [_("Order Number"), ", ".join([i.name for i in report.filter_order_ids])],
            [
                _("Store Code"),
                ", ".join(
                    [e.ref and e.ref or e.name for e in report.filter_partner_ids]
                ),
            ],
            [
                _("Payment Method"),
                ", ".join([e.name for e in report.filter_journal_ids]),
            ],
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

    def _get_payment_records(self, report):
        company = self.env.user.company_id
        params = {
            "date_format": company.report_date_format,
            "company_id": company.id,
            "payment_type": report.report_type,
        }
        query = """
WITH base_payment AS (
    SELECT
        ap.id AS id,
        ai.id AS invoice_id,
        ai.refund_invoice_id AS origin_invoice_id
    FROM account_payment ap
    JOIN account_journal aj ON aj.id = ap.journal_id
    LEFT JOIN account_invoice_payment_rel aipr ON aipr.payment_id = ap.id
    LEFT JOIN account_invoice ai ON aipr.invoice_id = ai.id
    JOIN res_partner rp ON rp.id = ai.partner_id
    WHERE ap.state = 'posted'
    AND ai.company_id = %(company_id)s
    AND ap.payment_type = %(payment_type)s
    AND ai.type IN ('out_invoice', 'out_refund')
        """
        if report.date_from:
            query += """
    AND ap.payment_date >= %(date_from)s
            """
            params.update({"date_from": str(report.date_from)})
        if report.date_to:
            query += """
    AND ap.payment_date <= %(date_to)s
            """
            params.update({"date_to": str(report.date_to)})
        if report.filter_order_ids:
            query += """
    AND ai.related_sale_order_id IN %(sale_order_ids)s
            """
            params.update({"sale_order_ids": tuple(report.filter_order_ids.ids)})
        if report.filter_partner_ids:
            query += """
    AND ap.partner_id IN %(partner_ids)s
            """
            params.update({"partner_ids": tuple(report.filter_partner_ids.ids)})
        query += """
),
related_payment AS (
    SELECT
        ap.id AS id
    FROM account_invoice_payment_rel aipr
    JOIN (
        SELECT ai.id
        FROM account_invoice ai
        JOIN base_payment bp ON
        """
        if report.report_type == "inbound":
            query += "bp.invoice_id = ai.refund_invoice_id"
        else:
            query += "bp.origin_invoice_id = ai.id"
        query += """
    ) origin_invoice ON aipr.invoice_id = origin_invoice.id
    JOIN account_payment ap on aipr.payment_id = ap.id
    WHERE ap.state = 'posted'
)
SELECT
    so.name AS order_number,
    rp.ref AS shop_code,
    rp.name shop_name,
    ap.payment_type AS payment_type,
    ai.number AS invoice_number,
    ai.type AS invoie_type,
    ai.state AS invoice_state,
    ai.mid AS mid,
    TO_CHAR(ai.date_invoice, %(date_format)s) AS date_invoice,
    ai.amount_total AS invoice_amount,
    ai.currency_id AS invoice_currency_id,
    ai.exchange_rate AS invoice_exchange_rate,
    aj.company_name AS journal_company_name,
    aj.name AS payment_method,
    TO_CHAR(ap.payment_date, %(date_format)s) AS payment_date,
    ap.amount AS payment_amount,
    ap.currency_id AS payment_currency_id,
    ap.ip_exchange_rate AS payment_exchange_rate,
    CASE
        WHEN ai.type = 'out_invoice' THEN ai.origin
        WHEN ai.type = 'out_refund' THEN rfd_ai.origin
    END AS invoice_origin
FROM
    account_payment ap
JOIN account_journal aj ON aj.id = ap.journal_id
LEFT JOIN account_invoice_payment_rel aipr ON aipr.payment_id = ap.id
JOIN account_invoice ai ON aipr.invoice_id = ai.id
LEFT JOIN account_invoice rfd_ai ON rfd_ai.id = ai.refund_invoice_id
JOIN res_partner rp ON rp.id = ai.partner_id
LEFT JOIN sale_order so ON so.id = ai.related_sale_order_id
WHERE ap.id in (
    SELECT id FROM base_payment
    UNION
    SELECT id FROM related_payment
)
        """
        if report.filter_journal_ids:
            query += """
AND aj.id IN %(journal_ids)s
            """
            params.update({"journal_ids": tuple(report.filter_journal_ids.ids)})
        query += """
ORDER BY
    order_number, invoice_number,
    shop_name, payment_date, ap.create_date
        """
        self._cr.execute(query, params)
        query_res = self._cr.dictfetchall()
        return query_res

    def _get_sheet_data(self, report):
        invoice_state_dict = {
            "draft": _("Draft"),
            "open": _("Open"),
            "in_payment": _("In Payment"),
            "paid": _("Paid"),
            "cancel": _("Cancelled"),
        }
        currency_jpy = self.env.ref("base.JPY")
        payments = self._get_payment_records(report)
        result = []
        for payment in payments:
            line = {}
            line["payment_flag"] = "P" if payment["payment_type"] == "inbound" else "R"
            # Display origin of the invoice as order number if the sale order
            # does not exist.
            line["order_number"] = (
                payment["order_number"] or payment["invoice_origin"] or ""
            )
            line["shop_code"] = payment["shop_code"] or ""
            line["shop_name"] = payment["shop_name"] or ""
            line["invoice_number"] = payment["invoice_number"] or ""
            line["mid"] = payment["mid"] or ""
            line["invoice_date"] = payment["date_invoice"] or ""
            line["invoice_amount"] = payment["invoice_amount"]
            line["invoice_amount_jpy"] = (
                payment["invoice_amount"]
                if payment["invoice_currency_id"] == currency_jpy.id
                else payment["invoice_amount"] * payment["invoice_exchange_rate"]
            ) or 0
            line["journal_company_name"] = payment["journal_company_name"] or ""
            line["payment_method"] = payment["payment_method"] or ""
            line["payment_date"] = payment["payment_date"] or ""
            line["payment_amount"] = payment["payment_amount"] or ""
            payment_amount_jpy = (
                payment["payment_amount"]
                if payment["payment_currency_id"] == currency_jpy.id
                else payment["payment_amount"] * payment["payment_exchange_rate"]
            ) or 0
            line["payment_amount_jpy"] = payment_amount_jpy
            line["payment_exchange_rate"] = payment["payment_exchange_rate"]
            # As the records are sorted by invoice_number,
            # reset the residual when last_invoice is different to the last
            # record. e.g. INV0001 -> INV0001
            # Otherwise, the residual will be inherited from last residual and
            # deducted/added by the current payment amount.
            last_invoice = (
                result[-1] and result[-1]["invoice_number"] if result else False
            )
            residual = (
                line["invoice_amount"]
                if payment["invoie_type"] == "out_invoice"
                else -line["invoice_amount"]
            )
            residual_jpy = (
                line["invoice_amount_jpy"]
                if payment["invoie_type"] == "out_invoice"
                else -line["invoice_amount_jpy"]
            )
            if last_invoice == line["invoice_number"]:
                residual = result[-1]["residual"]
                residual_jpy = result[-1]["residual_jpy"]
            factor = 1 if payment["payment_type"] == "inbound" else -1
            line["residual"] = residual - payment["payment_amount"] * factor
            line["residual_jpy"] = residual_jpy - payment_amount_jpy * factor
            line["status"] = invoice_state_dict[payment["invoice_state"]] or ""
            result.append(line)
        return result
