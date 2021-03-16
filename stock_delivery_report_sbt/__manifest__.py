# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Delivery Report",
    "version": "12.0.1.0.0",
    "category": "Warehouse",
    "author": "SB Technology Corp., Quartile Limited",
    "website": "https://www.quartile.co/",
    "license": "AGPL-3",
    "depends": [
        "account_report_menu_node_sbt",
        "report_xlsx_abstract_sbt",
        "sale_order_journal",
        "sale_order_unified_number",
        "stock_report_common_sbt",
    ],
    "data": ["wizard/stock_delivery_report_wizard_views.xml", "reports.xml"],
    "installable": True,
}
