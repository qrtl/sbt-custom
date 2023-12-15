# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.addons.component.core import AbstractComponent

import pytz


class EbisumartImportMapper(AbstractComponent):
    _name = 'ebisumart.import.mapper'
    _inherit = ['base.ebisumart.connector', 'base.import.mapper']
    _usage = 'import.mapper'


def normalize_datetime(field):
    """Change an invalid date which comes from Ebisumart, if
    no real date is set to null for correct import to
    Odoo."""

    def modifier(self, record, to_attr):
        raw_date = record[field]

        # If the date is invalid, return None
        if raw_date == '0000-00-00 00:00:00':
            return None

        # Convert the string to a naive datetime
        # Check if the datetime string has milliseconds
        if '.0' in raw_date:
            naive_dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S.%f")
        else:
            naive_dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")

        # Assume the naive datetime is in Japan's timezone
        user_timezone = pytz.timezone(self.env.user.tz)
        aware_dt = user_timezone.localize(naive_dt)

        # Convert the timezone-aware datetime to UTC
        utc_dt = aware_dt.astimezone(pytz.UTC)

        return utc_dt

    return modifier
