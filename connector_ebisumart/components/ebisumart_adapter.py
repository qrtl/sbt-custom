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

    def _generate_api_url(self, endpoint, params=None):
        """Generate the complete API URL using the given endpoint and params."""
        backend = self._get_backend()
        url = f"{backend.ebisumart_api_url}/{backend.ebisumart_number}/dataaccess{endpoint}.json"
        return url

    def _generate_headers(self):
        """Generate the headers required for the API request."""
        backend = self._get_backend()
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {backend.access_token}',
            'X-EBISU-API-VERSION': backend.api_version,
        }

    def _fetch_data(self, endpoint, params=None):
        """Common method to fetch data from Ebisumart."""
        url = self._generate_api_url(endpoint)
        headers = self._generate_headers()
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            # TODO: Add error handling
            pass

    def search(self, endpoint, attributes=None, filters=None):
        """Method to search data from Ebisumart, retrieving all pages."""
        records = []
        page = 1

        while True:
            params = {"result_count": 100}
            params["page"] = page
            if attributes:
                params["select"] = ",".join(attributes)

            if filters:
                params["query"] = json.dumps(filters)

            batch = self._fetch_data(endpoint, params)
            if not batch:
                break

            records.extend(batch)
            if len(batch) < 100:  # assuming a full page contains 100 records
                break

            page += 1

        return records

    
    def read(self, external_id, attributes=None):
        """
        Method to read a specific record from Ebisumart using its external ID.
        external_id: The ID of the record in Ebisumart.
        attributes: A list of attributes to select.
        """
        params ={}
        if attributes:
            params["select"] = ",".join(attributes)
        return self._fetch_data(external_id, params)
