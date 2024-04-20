import re

import odoo
import logging
from odoo import http

_logger = logging.getLogger(__name__)


db_filter_origin = http.db_filter


def db_filter(dbs, httprequest=None):
    dbs = db_filter_origin(dbs, httprequest)
    httprequest = httprequest or http.request.httprequest
    db_filter_hdr = httprequest.environ.get("HTTP_X_ODOO_DBFILTER")
    if db_filter_hdr:
        dbs = [db for db in dbs if re.match(db_filter_hdr, db)]
    return dbs


http.db_filter = db_filter

if 'bytekol_db_filter' not in odoo.tools.config.get('server_wide_modules', '').split(','):
    _logger.error('module bytekol_db_filter must be loaded in server_wide_modules')
