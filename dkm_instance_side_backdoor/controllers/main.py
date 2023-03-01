import logging
import werkzeug

import odoo
from odoo.exceptions import AccessDenied
from odoo.http import route, request, Controller
from odoo.service import security
from odoo.addons.web.controllers.main import _get_login_redirect_url

_logger = logging.getLogger(__name__)


class Main(Controller):

    @route('/super_user_login', auth='public', methods=['GET'])
    def supper_user_login(self, *args, **kwargs):
        token = kwargs.get('token')
        if not token:
            _logger.error('/super_user_login, not token.')
            return werkzeug.exceptions.Forbidden()
        _logger.error(token)
        valid_token = request.env['dkm.token'].sudo().is_token_valid(token, 'odoo_saas_api')
        if not valid_token:
            _logger.error('/super_user_login, token invalid.')
            return werkzeug.exceptions.Forbidden()
        valid_token.sudo().unlink()

        uid = request.session.uid = odoo.SUPERUSER_ID
        request.env['res.users'].clear_caches()
        request.session.session_token = security.compute_session_token(request.session, request.env)
        return request.redirect(_get_login_redirect_url(uid))

    @route('/default_admin_login', auth='public', methods=['GET'])
    def default_admin_login(self):
        try:
            request.session.authenticate(request.session.db, 'admin', 'admin')
            return request.redirect('/web')
        except AccessDenied:
            return request.redirect('/web/login')
