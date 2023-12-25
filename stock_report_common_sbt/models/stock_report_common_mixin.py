# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

from datetime import timedelta

from odoo import _, fields, models
from odoo.tools.misc import format_date

import pytz
from dateutil.relativedelta import relativedelta
from pytz import timezone


class StockReportCommonMixin(models.TransientModel):
    _name = "stock.report.common.mixin"

    # Convert datetime object to date string
    def _convert_to_user_date_string(self, datetime, hours, date_format=False):
        user_datetime = datetime + relativedelta(hours=hours)
        if not date_format:
            date_format = self.env.user.company_id.report_date_format
        return format_date(self.env, user_datetime, date_format=date_format)

    # Convert date string with timestamp to datetime object
    def _convert_to_user_datetime_string(self, date, timestamp, hours):
        datetime_value = fields.Datetime.from_string("{} {}".format(date, timestamp))
        return fields.Datetime.to_string(datetime_value - relativedelta(hours=hours))

    # Return the time difference (in hours), e.g. if user's timezone is in
    # GMT+9 this method will return 9.0
    def _get_tz_hours_diff(self):
        tz = timezone(self.env.user.tz or "UTC")
        current_time = fields.Datetime.now()
        user_time = pytz.utc.localize(current_time).astimezone(tz)
        utc_time = timezone("UTC").localize(current_time)
        hours_diff = (
            (user_time.utcoffset() - utc_time.utcoffset()) / timedelta(minutes=1) / 60
        )
        return hours_diff

    def _get_invoice_line_vals(self, query_res):
        invoice_state_dict = {
            "draft": _("Draft"),
            "open": _("Open"),
            "in_payment": _("In Payment"),
            "paid": _("Paid"),
        }
        currency_jpy = self.env.ref("base.JPY")
        exchange_rate = query_res["exchange_rate"] or 1
        amount = amount_jpy = query_res["amount"]
        tax_amount = tax_amount_jpy = query_res["tax_amount"]
        if query_res["currency_id"] and currency_jpy.id != query_res["currency_id"]:
            amount_jpy = amount * exchange_rate
            tax_amount_jpy = tax_amount * exchange_rate
        return {
            "price_unit": query_res["price_unit"],
            "amount": amount,
            "tax_amount": tax_amount,
            "amount_jpy": amount_jpy,
            "tax_amount_jpy": tax_amount_jpy,
            "exchange_rate": exchange_rate,
            "invoice_number": query_res["invoice_number"],
            "status": query_res["status"]
            and invoice_state_dict[query_res["status"]]
            or "",
        }

    def _get_move_ids(self, report):
        company = self.env.user.company_id
        hours_diff = self._get_tz_hours_diff()
        query = """
WITH base_move AS (
    SELECT
        sm.id AS id,
        sm.group_id AS group_id
    FROM stock_move sm
    JOIN stock_picking sp ON sp.id = sm.picking_id
    JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
    JOIN procurement_group pg ON pg.id = sm.group_id
    WHERE sm.state = 'done'
    AND sm.company_id = %s
    AND spt.code = %s
"""
        params = [company.id, report.report_type]
        if report._name == "stock.delivery.report":
            query += """
    AND pg.sale_id IS NOT NULL
"""
        else:
            query += """
    AND sm.purchase_line_id IS NOT NULL
"""
        if report.date_from:
            date_from = self._convert_to_user_datetime_string(
                report.date_from, "00:00:00", hours_diff
            )
            query += """
    AND sp.scheduled_date >= %s
            """
            params.append(date_from)
        if report.date_to:
            date_to = self._convert_to_user_datetime_string(
                report.date_to, "23:59:59", hours_diff
            )
            query += """
    AND sp.scheduled_date <= %s
        """
            params.append(date_to)
        if report.filter_picking_partner_ids:
            query += """
    AND sp.partner_id IN %s
        """
            params.append(tuple(report.filter_picking_partner_ids.ids))
        if report._name == "stock.receipt.report" and report.filter_product_ids:
            query += """
    AND sm.product_id IN %s
        """
            params.append(tuple(report.filter_product_ids.ids))
        query += """
),
related_move AS (
    SELECT
        sm.id AS id
    FROM stock_move sm
    WHERE sm.group_id IN (
        SELECT group_id FROM base_move
    )
    AND sm.state = 'done'
)
SELECT
    sm.id AS move_id
FROM
    stock_move sm
WHERE
    sm.id in (
        SELECT id FROM base_move
        UNION
        SELECT id FROM related_move
    )
"""
        self._cr.execute(query, params)
        return [item[0] for item in self._cr.fetchall()]

    def _get_product_ids(self, move_ids):
        query = """
SELECT
    DISTINCT pt.id
FROM
    stock_move sm
JOIN product_product pp ON pp.id = sm.product_id
JOIN product_template pt ON pt.id = pp.product_tmpl_id
WHERE
    sm.id IN %s
"""
        params = [tuple(move_ids)]
        self._cr.execute(query, params)
        return [item[0] for item in self._cr.fetchall()]

    def _get_product_info_dict(self, product_ids):
        query = """
SELECT
    pt.id AS product_id,
    ps.name AS supplier_id,
    ps.product_code AS supplier_product_code
FROM
    product_template pt
JOIN product_supplierinfo ps ON ps.product_tmpl_id = pt.id
WHERE pt.id IN %s
AND ps.product_code IS NOT NULL
ORDER BY
    pt.id, ps.name, ps.sequence
"""
        params = [tuple(product_ids)]
        self._cr.execute(query, params)
        query_res = self._cr.dictfetchall()
        product_info_dict = {}
        for res in query_res:
            if res["product_id"] not in product_info_dict:
                product_info_dict[res["product_id"]] = {}
            if res["supplier_id"] not in product_info_dict[res["product_id"]]:
                product_info_dict[res["product_id"]][res["supplier_id"]] = res[
                    "supplier_product_code"
                ]
        return product_info_dict
