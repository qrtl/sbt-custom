# Copyright 2020 SB Technology Corp.
# Copyright 2020 Quartile Limited
{
    "name": "Account Payment Import",
    "version": "12.0.1.0.1",
    "category": "Accounting",
    "author": "SB Technology Corp., Quartile Limited",
    "website": "https://www.quartile.co/",
    "depends": ["account_accountant", "base_import_log", "purchase", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/account_invoice_views.xml",
        "views/payment_import_views.xml",
        "views/account_payment_views.xml",
        "views/error_log_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
