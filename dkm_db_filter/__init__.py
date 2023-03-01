import re
from odoo import http

db_filter_origin = http.db_filter


def db_filter(dbs, httprequest=None):
    dbs = db_filter_origin(dbs, httprequest)
    httprequest = httprequest or http.request.httprequest
    db_filter_hdr = httprequest.environ.get("HTTP_X_ODOO_DBFILTER")
    if db_filter_hdr:
        dbs = [db for db in dbs if re.match(db_filter_hdr, db)]
    return dbs


http.db_filter = db_filter
