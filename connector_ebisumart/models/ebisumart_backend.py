# Copyright 2023 Quartile Limited

from odoo import fields, models
from datetime import datetime, timedelta
import base64
import requests


class EbisumartBackend(models.Model):
    _name = 'ebisumart.backend'
    _inherit = 'connector.backend'
    _description = 'Ebisumart Backend'
    
    # fields and methods specific to our backend
    name = fields.Char()
    ebisumart_number = fields.Char(string='Ebisumart No')
    app_code = fields.Char()
    password = fields.Char()
    root_ebisumart_url = fields.Char()
    access_token = fields.Char()
    refresh_token = fields.Char()
    token_expiration = fields.Datetime()
    redirect_uri = fields.Char()
    shop_id = fields.Char()

    def get_authorize_url(self):
        root_url = self.root_ebisumart_url
        root_url += self.ebisumart_number + "/admin_authorize.html"
        redirect_uri = self.redirect_uri
        authorize_url = f"{root_url}?scope=item privacy system&response_type=code&redirect_uri={redirect_uri}&client_id={self.app_code}"
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
        oauth_url = f"https://demo-service-api.ebisumart.com/{self.ebisumart_number}/app_oauth/access_token.html"
        
        # Define the Headers
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode((self.app_code + ':' + self.password).encode()).decode()
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
        
        # Check the response
        if response.status_code == 200:
            # Parse the response
            response_data = response.json()
            
            # Save the token in the backend record
            self.access_token = response_data['access_token']
            self.refresh_token = response_data['refresh_token']
            expiry_time = datetime.now() + timedelta(seconds=response_data['expires_in'])
            self.token_expiration = expiry_time.strftime('%Y-%m-%d %H:%M:%S')
            self.shop_id = response_data['shop_id']
        else:
            # TODO: Handle the error case
            pass

    def refresh_oauth_token(self):
        """Refresh the OAuth2.0 token"""
        # Check if the token is expired
        if datetime.now() >= self.token_expiration:
            # TODO: Refresh the token using the Refresh Token
            pass