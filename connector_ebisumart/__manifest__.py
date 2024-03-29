# Copyright 2023 Quartile Limited
{
    "name": "Connector Ebisumart",
    "version": "12.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Connector",
    "license": "AGPL-3",
    "depends": [
        "purchase",
        "connector_ecommerce",
        "sale_order_journal",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/automatic_workflow_data.xml",
        "data/scheduler.xml",
        "views/account_journal_views.xml",
        "views/ebisumart_backend_views.xml",
        "views/product_product_views.xml",
        "views/connector_ebisumart_menu_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
}
