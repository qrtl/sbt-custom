# Copyright 2023 Quartile Limited

from odoo import fields, models

class EbisumartBackend(models.Model):
    _name = 'ebisumart.backend'
    _inherit = 'connector.backend'
    _description = 'Ebisumart Backend'
    
    # fields and methods specific to our backend
