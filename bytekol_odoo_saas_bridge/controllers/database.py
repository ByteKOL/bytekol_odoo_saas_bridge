import logging
import psycopg2
from werkzeug.wrappers import Response

import odoo
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)
from odoo.addons.web.controllers.main import Database as OdooControllerDB


def _can_connect_to_postgres() -> bool:
    """Check if PostgreSQL server is reachable."""
    try:
        db = odoo.sql_db.db_connect('postgres')
        with db.cursor():
            pass
        return True
    except psycopg2.OperationalError:
        return False

DB_CONNECTION_ERROR_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>Database Connection Error</title>
    <link rel="stylesheet" href="/web/static/lib/bootstrap/dist/css/bootstrap.css"/>
</head>
<body>
    <div class="container mt-5">
        <div class="text-center">
            <div class="alert alert-danger" role="alert">
                <div class="alert-heading">Cannot connect to PostgreSQL database.</div>
                <p class="mb-0">
                    <a href="/" class="alert-link">Retry</a>
                </p>
            </div>
        </div>
    </div>
</body>
</html>'''



class Database(OdooControllerDB):

    @http.route('/db_connection_error', type='http', auth='none')
    def db_connection_error(self, **kw):
        """Display error page when PostgreSQL connection fails."""
        if not _can_connect_to_postgres():
            return Response(DB_CONNECTION_ERROR_HTML, mimetype='text/html')
        else:
            return request.redirect('/')

    @http.route('/web/database/selector', type='http', auth="none")
    def selector(self, **kw):
        if not _can_connect_to_postgres():
            return request.redirect('/db_connection_error', 303)
        return super().selector(**kw)

    @http.route('/web/database/manager', type='http', auth="none")
    def manager(self, **kw):
        if not _can_connect_to_postgres():
            return request.redirect('/db_connection_error', 303)
        return super().manager(**kw)
