# Copyright 2023 Quartile Limited
{
    "name": "Connector Ebisumart",
    "version": "12.0.1.0.0",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "category": "Connector",
    "license": "AGPL-3",
    "depends": ["connector_ecommerce"],
    "data": [
        "security/ir.model.access.csv",
        "data/scheduler.xml",
        "views/ebisumart_backend_views.xml",
        # "views/product_category_views.xml",
        "views/product_product_views.xml",
        "views/connector_ebisumart_menu_views.xml",
    ],
    "installable": True,
}