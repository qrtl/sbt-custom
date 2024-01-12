# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime, timedelta

from odoo import api, fields, models

from odoo.addons.connector.models.checkpoint import add_checkpoint

import requests


class EbisumartBackend(models.Model):
    _name = 'ebisumart.backend'
    _inherit = 'connector.backend'
    _description = 'Ebisumart Backend'

    # fields and methods specific to our backend
    name = fields.Char(required=True)
    ebisumart_number = fields.Char(required=True, string='Ebisumart No')
    app_code = fields.Char(required=True)
    password = fields.Char(required=True)
    root_ebisumart_url = fields.Char(required=True)
    ebisumart_access_url = fields.Char(required=True)
    ebisumart_api_url = fields.Char(required=True)
    api_version = fields.Char(default='1')
    redirect_uri = fields.Char(required=True)
    sale_partner_id = fields.Many2one(
        "res.partner",
        required=True,
        domain="[('customer','=',True)]"
    )
    coupon_product_id = fields.Many2one("product.product", required=True)
    access_token = fields.Char()
    refresh_token = fields.Char()
    token_expiration = fields.Datetime()
    shop_id = fields.Char()
    last_fetch_product_date = fields.Datetime()
    last_fetch_order_date = fields.Datetime()

    def get_authorize_url(self):
        root_url = self.root_ebisumart_url
        root_url += "/" + self.ebisumart_number + "/admin_authorize.html"
        redirect_uri = self.redirect_uri
        authorize_url = (
            f"{root_url}?scope=item privacy system&response_type=code"
            f"&redirect_uri={redirect_uri}&client_id={self.app_code}"
        )
        return authorize_url

    def open_authorization_url(self):
        """Open the authorization URL in a new browser tab"""
        # Get the authorization URL
        authorize_url = self.get_authorize_url()

        # Return an action to open this URL in a new tab
        return {
            'type': 'ir.actions.act_url',
            'url': authorize_url,
            'target': 'new',
        }

    def get_token(self, auth_code):
        """Retrieve token"""
        # Define the API Endpoint
        oauth_url = (
            f"{self.ebisumart_access_url}"
            f"/app_oauth/access_token.html"
        )

        # Define the Headers
        auth_string = (self.app_code + ':' + self.password).encode()
        encoded_auth_string = base64.b64encode(auth_string).decode()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_auth_string}'
        }

        # Define the payload
        payload = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.app_code
        }

        # Make the POST request
        response = requests.post(oauth_url, data=payload, headers=headers)
        response.raise_for_status()

        # Check the response
        if response.status_code == 200:
            # Parse the response
            response_data = response.json()

            # Save the token in the backend record
            self.access_token = response_data['access_token']
            self.refresh_token = response_data['refresh_token']
            expiry_time = datetime.now() + timedelta(
                seconds=response_data['expires_in']
            )
            self.token_expiration = expiry_time.strftime('%Y-%m-%d %H:%M:%S')
            self.shop_id = response_data['shop_id']

    def refresh_oauth_token(self):
        """Refresh the token"""
        # Check if the token is expired
        backend = self.env['ebisumart.backend'].sudo().search([])[0]
        oauth_url = (
            f"{backend.ebisumart_access_url}"
            f"/app_oauth/access_token.html"
        )

        # Define the Headers
        auth_string = (backend.app_code + ':' + backend.password).encode()
        encoded_auth_string = base64.b64encode(auth_string).decode()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + encoded_auth_string
        }

        # Define the payload
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': backend.refresh_token,
            'client_id': backend.app_code
        }

        # Make the POST request
        response = requests.post(oauth_url, data=payload, headers=headers)
        response.raise_for_status()

        # Check the response
        if response.status_code == 200:
            # Parse the response
            response_data = response.json()

            # Save the token in the backend record
            backend.access_token = response_data['access_token']
            expiry_time = datetime.now() + timedelta(
                seconds=response_data['expires_in']
            )
            backend.token_expiration = expiry_time.strftime('%Y-%m-%d %H:%M:%S')

    @api.multi
    def add_checkpoint(self, record):
        self.ensure_one()
        record.ensure_one()
        return add_checkpoint(self.env, record._name, record.id,
                              self._name, self.id)

    @api.multi
    def _import_orders(self, model):
        for backend in self:
            self.env[model].with_delay().import_batch(
                backend,
                filters=None
            )

    @api.multi
    def _import_partners(self, model):
        for backend in self:
            self.env[model].with_delay().import_batch(
                backend,
                filters=None
            )

    @api.multi
    def _import_products(self, model):
        for backend in self:
            self.env[model].with_delay().import_batch(
                backend,
                filters=None
            )

    @api.multi
    def import_products(self):
        self._import_products('ebisumart.product.product')
        return True

    @api.multi
    def import_sale_orders(self):
        self._import_orders('ebisumart.sale.order')
        return True

    @api.multi
    def import_partners(self):
        self._import_partners('ebisumart.res.partner')
        return True

    @api.model
    def _ebisumart_backend(self, callback, domain=None):
        if domain is None:
            domain = []
        backends = self.search(domain)
        if backends:
            getattr(backends, callback)()

    @api.model
    def _scheduler_import_products(self, domain=None):
        self._ebisumart_backend('import_products', domain=domain)

    @api.model
    def _scheduler_import_orders(self, domain=None):
        self._ebisumart_backend('import_sale_orders', domain=domain)

    @api.model
    def _scheduler_import_partners(self, domain=None):
        self._ebisumart_backend('import_partners', domain=domain)
