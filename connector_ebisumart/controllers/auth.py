# Copyright 2023 Quartile Limited

from odoo import http
from odoo.http import request


class EbisumartAuth(http.Controller):
    # TODO: add error message control
    @http.route('/ebisumart/auth', type='http', auth="public", csrf=False)
    def ebisumart_auth_redirect(self, **kwargs):
        code = kwargs.get('code')
        if code:
            # We have an authorization code, so now we get the token.
            # Assuming we only have one backend.
            backend = request.env['ebisumart.backend'].sudo().search([])[0]
            if backend:
                backend.get_token(code)
        return 'Success'
