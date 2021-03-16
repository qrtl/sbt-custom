# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Receipt Report",
    "version": "12.0.1.0.0",
    "category": "Warehouse",
    "author": "SB Technology Corp., Quartile Limited",
    "website": "https://www.quartile.co/",
    "license": "AGPL-3",
    "depends": [
        "account_report_menu_node_sbt",
        "purchase_stock",
        "report_xlsx_abstract_sbt",
        "sale_stock",
        "stock_report_common_sbt",
    ],
    "data": ["wizard/stock_receipt_report_wizard_views.xml", "reports.xml"],
    "installable": True,
}
