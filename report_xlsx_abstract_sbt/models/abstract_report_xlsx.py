# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited

import datetime

from odoo import models
from odoo.tools import format_date


class AbstractReportXlsx(models.TransientModel):
    _name = "report.report_xlsx_abstract_sbt.abstract_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        self = self.with_context(lang=self.env.user.lang)

        report = objects

        self.row_pos = 0

        self._define_formats(workbook)

        report_name = self._get_report_name(report)
        filters = self._get_report_filters(report)
        self.columns = self._get_report_columns(report)
        self.workbook = workbook
        self.sheet = workbook.add_worksheet(report_name[:31])

        self._set_column_width()

        self._write_report_title(report_name)

        self._write_filters(filters)

        self._generate_report_content(workbook, report)

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Those formats can be used on all cell.
        Available formats are :
         * format_bold
         * format_right
         * format_right_bold_italic
         * format_header_left
         * format_header_center
         * format_header_right
         * format_header_amount_company
         * format_amount_company
         * format_amount (no dp)
         * format_percent_bold_italic
         * format_exchange_rate (8 dp)
         * format_quantity (no dp)
        """
        self.format_bold = workbook.add_format({"bold": True})
        self.format_right = workbook.add_format({"align": "right"})
        self.format_left = workbook.add_format({"align": "left"})
        self.format_right_bold_italic = workbook.add_format(
            {"align": "right", "bold": True, "italic": True}
        )
        self.format_header_left = workbook.add_format(
            {"bold": True, "border": True, "bg_color": "#FFFFCC"}
        )
        self.format_header_center = workbook.add_format(
            {"bold": True, "align": "center", "border": True, "bg_color": "#FFFFCC"}
        )
        self.format_header_right = workbook.add_format(
            {"bold": True, "align": "right", "border": True, "bg_color": "#FFFFCC"}
        )
        # Company Amount Format
        self.format_header_amount_company = workbook.add_format(
            {"bold": True, "border": True, "bg_color": "#FFFFCC"}
        )
        currency_id = self.env["res.company"]._get_user_currency()
        if not currency_id.decimal_places:
            company_amount_format = "#,##0"
        else:
            company_amount_format = "#,##0." + "0" * currency_id.decimal_places
        self.format_header_amount_company.set_num_format(company_amount_format)
        self.format_amount_company = workbook.add_format()
        self.format_amount_company.set_num_format(company_amount_format)
        self.format_amount_company_bold = workbook.add_format({"bold": True})
        self.format_amount_company_bold.set_num_format(company_amount_format)
        # Percent Format
        self.format_percent_bold_italic = workbook.add_format(
            {"bold": True, "italic": True}
        )
        self.format_percent_bold_italic.set_num_format("#,##0.00%")
        # Exchange rate Format
        self.format_exchange_rate = workbook.add_format()
        self.format_exchange_rate.set_num_format("#,##0.00000000")
        # Standard amount Format
        self.format_amount = workbook.add_format()
        self.format_amount.set_num_format("#,##0")
        # Quantity Format
        self.format_quantity = workbook.add_format()
        self.format_quantity.set_num_format("#,##0")

    def _set_column_width(self):
        """Set width for all defined columns.
        Columns are defined with `_get_report_columns` method.
        """
        for position, column in self.columns.items():
            self.sheet.set_column(position, position, column["width"])

    def _write_report_title(self, title):
        """Write report title on current line using all defined columns width.
        Columns are defined with `_get_report_columns` method.
        """
        self.sheet.merge_range(
            self.row_pos,
            0,
            self.row_pos,
            len(self.columns) - 1,
            title,
            self.format_bold,
        )
        self.row_pos += 2

    def _write_filters(self, filters):
        """Write one line per filters on starting on current line.
        Columns number for filter name is defined
        with `_get_col_count_filter_name` method.
        Columns number for filter value is define
        with `_get_col_count_filter_value` method.
        """
        col_name = 1
        col_count_filter_name = self._get_col_count_filter_name()
        col_count_filter_value = self._get_col_count_filter_value()
        col_value = col_name + col_count_filter_name + 1
        for title, value in filters:
            if col_count_filter_name == 1:
                self.sheet.write(
                    self.row_pos, col_name, title, self.format_header_left,
                )
            else:
                self.sheet.merge_range(
                    self.row_pos,
                    col_name,
                    self.row_pos,
                    col_name + col_count_filter_name - 1,
                    title,
                    self.format_header_left,
                )
            if col_count_filter_value == 1:
                self.sheet.write(self.row_pos, col_name + col_count_filter_value, value)
            else:
                self.sheet.merge_range(
                    self.row_pos,
                    col_value,
                    self.row_pos,
                    col_value + col_count_filter_value - 1,
                    value,
                )
            self.row_pos += 1
        self.row_pos += 2

    def write_array_header(self):
        """Write array header on current line using all defined columns name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.items():
            self.sheet.write(
                self.row_pos, col_pos, column["header"], self.format_header_center
            )
        self.row_pos += 1

    def write_line(self, line_object):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.items():
            value = line_object.get(column["field"])
            if isinstance(value, datetime.date):
                value = format_date(self.env, value)
            cell_type = column.get("type", "string")
            if cell_type == "many2one":
                self.sheet.write_string(
                    self.row_pos, col_pos, value.name or "", self.format_right
                )
            elif cell_type == "string":
                self.sheet.write_string(self.row_pos, col_pos, value or "")
            elif cell_type == "amount":
                self.sheet.write_number(
                    self.row_pos,
                    col_pos,
                    value and float(value) or 0,
                    self.format_amount,
                )
            elif cell_type == "amount_company":
                self.sheet.write_number(
                    self.row_pos,
                    col_pos,
                    value and float(value) or 0,
                    self.format_amount_company,
                )
            elif cell_type == "quantity":
                self.sheet.write_number(
                    self.row_pos,
                    col_pos,
                    value and float(value) or 0,
                    self.format_quantity,
                )
            elif cell_type == "exchange_rate":
                self.sheet.write_number(
                    self.row_pos,
                    col_pos,
                    value and float(value) or 0,
                    self.format_exchange_rate,
                )
            elif cell_type == "amount_currency":
                if line_object.currency_id:
                    format_amt = self._get_currency_amt_format(line_object)
                    self.sheet.write_number(
                        self.row_pos, col_pos, value and float(value) or 0, format_amt
                    )
        self.row_pos += 1

    def _generate_report_content(self, workbook, report):
        """
            Allow to fetch report content to be displayed.
        """
        raise NotImplementedError()

    def _get_report_name(self, report):
        """
            Allow to define the report name.
            Report name will be used as sheet name and as report title.
            :return: the report name
        """
        raise NotImplementedError()

    def _get_report_footer(self):
        """
            Allow to define the report footer.
            :return: the report footer
        """
        return False

    def _get_report_columns(self, report):
        """
            Allow to define the report columns
            which will be used to generate report.
            :return: the report columns as dict
            :Example:
            {
                0: {'header': 'Simple column',
                    'field': 'field_name_on_my_object',
                    'width': 11},
                1: {'header': 'Amount column',
                     'field': 'field_name_on_my_object',
                     'type': 'amount',
                     'width': 14},
            }
        """
        raise NotImplementedError()

    def _get_report_filters(self, report):
        """
            :return: the report filters as list
            :Example:
            [
                ['first_filter_name', 'first_filter_value'],
                ['second_filter_name', 'second_filter_value']
            ]
        """
        raise NotImplementedError()

    def _get_col_count_filter_name(self):
        """
            :return: the columns number used for filter names.
        """
        raise NotImplementedError()

    def _get_col_count_filter_value(self):
        """
            :return: the columns number used for filter values.
        """
        raise NotImplementedError()

    def _convert_filter_date_string(self, date, date_format=False):
        if not date_format:
            date_format = self.env.user.company_id.report_date_format
        return format_date(self.env, date, date_format=date_format)
