import logging
import threading

import odoo
from odoo.exceptions import AccessDenied
from odoo.http import route, request, Controller
from odoo.modules.registry import Registry
from odoo.service import security
from odoo.addons.web.controllers.main import _get_login_redirect_url
from odoo.addons.dkm_api.api import dkm_api, verify_admin_password

_logger = logging.getLogger(__name__)


class Main(Controller):

    @dkm_api('odoo_saas_api', custom_response=True, one_time_token=True, token_on='url_params')
    @route('/super_user_login', auth='public', methods=['GET'])
    def supper_user_login(self):
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

    @verify_admin_password
    @route('/reload_registry', type='json', auth='none', methods=['POST'])
    def reload_registry(self):
        json_data = request.jsonrequest
        db_name = json_data.get('db_name')
        wait = json_data.get('wait')

        def _reload_registry():
            Registry.new(db_name, update_module=True)

        if not wait:
            threading.Thread(target=_reload_registry).start()
        else:
            _reload_registry()
        return {'success': True}

    @verify_admin_password
    @route('/download_backup', type='http', auth='none', methods=['POST'])
    def download_backup(self):
        pass
