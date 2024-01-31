# Part of Pactera. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def name_get(self):
        return [
            (
                partner.id,
                partner.ref
                and partner.name + str(partner.ref and " [" + partner.ref + "]" or "")
                or partner.name,
            )
            for partner in self
        ]
