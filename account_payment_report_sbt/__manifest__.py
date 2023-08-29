# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
{
    "name": "Account Payment Report",
    "version": "12.0.1.0.2",
    "category": "Accounting",
    "author": "SB Technology Corp., Quartile Limited",
    "website": "https://www.quartile.co",
    "license": "AGPL-3",
    "depends": [
        "account_report_menu_node_sbt",
        "report_xlsx_abstract_sbt",
        "sale_order_unified_number",
    ],
    "data": [
        "views/account_journal_views.xml",
        "wizard/account_payment_report_wizard_views.xml",
        "reports.xml",
    ],
    "installable": True,
}
