# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.addons.component.core import AbstractComponent
from datetime import timedelta
import requests
from pytz import timezone
import pytz


class EbisumartCRUDAdapter(AbstractComponent):
    _name = 'ebisumart.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.ebisumart.connector']
    _usage = 'backend.adapter'

    def search(self, endpoint, attributes=None, filters=None):
        """ Search records according to some filters """
        raise NotImplementedError

    # pylint: disable=W8106
    def read(self, external_id, attributes=None):
        """ Returns the detailed information for record """
        raise NotImplementedError

    # pylint: disable=W8106
    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    # pylint: disable=W8106
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
        url = (
            f"{backend.ebisumart_api_url}"
            f"/dataaccess{endpoint}.json"
        )
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
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()

    def _get_filters(self, last_fetch_date):
        # Add a one-day buffer
        buffer_time = timedelta(days=1)
        last_fetch_date = last_fetch_date - buffer_time
        user_tz = self.env.user.tz or 'UTC'
        local_tz = timezone(user_tz)
        # Convert last_fetch_date from UTC to the user's timezone
        fetch_date = pytz.utc.localize(last_fetch_date).astimezone(local_tz)
        last_fetch_date_str = fetch_date.strftime('%Y/%m/%d %H:%M:%S')
        regist_date_filter = {
            "column": "REGIST_DATE",
            "operator": "more_than_equals",
            "to_char_format": "YYYY/MM/DD HH24:MI:SS",
            "value": last_fetch_date_str
        }
        update_date_filter = {
            "column": "UPDATE_DATE",
            "operator": "more_than_equals",
            "to_char_format": "YYYY/MM/DD HH24:MI:SS",
            "value": last_fetch_date_str
        }
        filters = [
            {
                "operator": "or",
                "operand": [regist_date_filter, update_date_filter]
            }
        ]
        return filters

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

    # pylint: disable=W8106
    def read(self, external_id, attributes=None):
        """
        Method to read a specific record from Ebisumart using its external ID.
        external_id: The ID of the record in Ebisumart.
        attributes: A list of attributes to select.
        """
        params = {}
        if attributes:
            params["select"] = ",".join(attributes)
        return self._fetch_data(external_id, params)
