# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
import requests
import json


class EbisumartCRUDAdapter(AbstractComponent):
    _name = 'ebisumart.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.ebisumart.connector']
    _usage = 'backend.adapter'

    def search(self, endpoint, attributes=None, filters=None):
        """ Search records according to some filters """
        raise NotImplementedError

    def read(self, external_id, attributes=None):
        """ Returns the detailed information for record """
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, external_id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, external_id):
        """ Delete a record on the external system """
        raise NotImplementedError

class EbisumartAdapater(AbstractComponent):
    _name = "ebisumart.adapter"
    _inherit = "ebisumart.crud.adapter"

    def _get_backend(self):
        return self.backend_record
    
    def _generate_api_url(self, endpoint, attributes=None):
        """
        Generate the complete API URL using the given endpoint and attributes.
        """
        backend = self._get_backend()
        url = f"https://{backend.ebisumart_api_url}/{backend.ebisumart_number}/dataaccess{endpoint}.json"

        if attributes:
            # If specific attributes are to be selected, add them to the URL
            attributes_query = ','.join(attributes)
            url += f"?select={attributes_query}"

        return url

    def _generate_headers(self):
        """
        Generate the headers required for the API request.
        """
        backend = self._get_backend()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {backend.access_token}',
            'X-EBISU-API-VERSION': backend.api_version,
        }
        return headers

    def _fetch_data(self, endpoint, attributes=None):
        """
        Common method to fetch data from Ebisumart.
        endpoint: The API endpoint.
        attributes: A list of attributes to select.
        """
        url = self._generate_api_url(endpoint, attributes)
        headers = self._generate_headers()

        # Make the GET request
        response = requests.get(url, headers=headers)

        # Check the response status
        if response.status_code == 200:
            return response.json()  # Return the JSON content of the response
        else:
            # TODO: Add error handling
            pass

    def search(self, endpoint, attributes=None, filters=None):
        """
        Method to search data from Ebisumart.
        endpoint: The API endpoint, e.g. "/items".
        attributes: A list of attributes to select.
        filters: A dictionary of filters to apply to the search.
        """
        # Prepare the endpoint by adding filters if any.
        if filters:
            # Convert the Python dictionary to a JSON string
            query_str = json.dumps(filters)
            endpoint += f"&query={query_str}"
        return self._fetch_data(endpoint, attributes)

    def read(self, external_id, attributes=None):
        """
        Method to read a specific record from Ebisumart using its external ID.
        external_id: The ID of the record in Ebisumart.
        attributes: A list of attributes to select.
        """
        return self._fetch_data(external_id, attributes)
