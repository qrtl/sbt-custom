# Part of Pactera. See LICENSE file for full copyright and licensing details.

{
    "name": "SBT - Sales",
    "version": "12.0.1.0.0",
    "category": "Sales",
    "sequence": 5,
    "summary": "",
    "author": "Pactera, Quartile Limited",
    "company": "Pactera",
    "website": "https://www.quartile.co",
    "depends": [
        "account_report_menu_node_sbt",
        "account_accountant",
        "sale_order_unified_number",
        "stock",
    ],
    "data": ["views/account_journal_views.xml", "views/account_invoice_views.xml"],
    "installable": True,
    "application": True,
    "auto_install": False,
}
