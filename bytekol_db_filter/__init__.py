import re

import odoo
import logging
from odoo import http

_logger = logging.getLogger(__name__)


db_filter_origin = http.db_filter


def db_filter(dbs, host=None):
    httprequest = http.request.httprequest
    db_filter_hdr = httprequest.environ.get("HTTP_X_ODOO_DBFILTER")
    if db_filter_hdr:
        return [db_filter_hdr]
    else:
        return db_filter_origin(dbs, host)


http.db_filter = db_filter

if 'bytekol_db_filter' not in odoo.tools.config.get('server_wide_modules', []):
    _logger.error('module bytekol_db_filter must be loaded in server_wide_modules')
