import datetime
import json
import logging
import os
import tempfile
import threading
import traceback

import werkzeug

import odoo
from odoo import _
from odoo.addons.bytekol_odoo_saas_bridge import api
from odoo.addons.bytekol_odoo_saas_bridge.db import dump_db
from odoo.exceptions import AccessDenied, UserError
from odoo.http import route, request, Controller, content_disposition
from odoo.modules.registry import Registry
from odoo.service import security
from odoo.addons.web.controllers.utils import _get_login_redirect_url

_logger = logging.getLogger(__name__)


class Main(Controller):

    @api.bk_api('odoo_saas_api', custom_response=True, one_time_token=True, token_on='url_params')
    @route('/super_user_login', auth='public', methods=['GET'])
    def supper_user_login(self):
        uid = request.session.uid = odoo.SUPERUSER_ID
        request.env.registry.clear_cache()
        request.session.session_token = security.compute_session_token(request.session, request.env)
        return request.redirect(_get_login_redirect_url(uid))

    @api.bk_api('odoo_saas_api', custom_response=True, one_time_token=True, token_on='url_params')
    @route('/saas_bridge_user_login', auth='public', methods=['GET'], type='http')
    def saas_bridge_user_login(self, **kwargs):
        user = request.env['res.users'].browse(int(kwargs['user_id']))
        uid = request.session.uid = int(kwargs['user_id'])
        request.env.registry.clear_cache()
        request.session.session_token = security.compute_session_token(request.session, request.env)
        if user.sudo().has_groups('base.group_portal'):
            return request.redirect('/')
        return request.redirect(_get_login_redirect_url(uid))

    @route('/default_admin_login', auth='public', methods=['GET'])
    def default_admin_login(self):
        try:
            request.session.authenticate(request.session.db, {
                'login': 'admin', 'password': 'admin', 'type': 'password'
            })
            return request.redirect('/web')
        except AccessDenied:
            return request.redirect('/web/login')

    @api.verify_admin_password
    @route('/reload_registry', type='jsonrpc', auth='none', methods=['POST', 'GET'])
    def reload_registry(self):
        json_data = request.get_json_data()
        db_name = json_data.get('db_name')
        wait = json_data.get('wait')

        def _reload_registry():
            Registry.new(db_name, update_module=True)

        if not wait:
            threading.Thread(target=_reload_registry).start()
        else:
            _reload_registry()
        return {'success': True}

    @api.bk_api('odoo_saas_api', custom_response=True, one_time_token=True, token_on='url_params')
    @route('/download_backup', type='http', auth='public', methods=['GET'])
    def download_backup(self, db_name, backup_format='zip'):
        """
        :param db_name:
        :param backup_format: 'zip', 'db', 'filestore'
        :return:
        """

        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        file_format = '.zip'
        if backup_format == 'db':
            file_format = '.sql'

        filename = "%s_%s.%s" % (db_name, ts, file_format)
        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', content_disposition(filename)),
        ]
        if backup_format in ['zip', 'db']:
            dump_stream = dump_db(db_name, None, backup_format)
        elif backup_format == 'filestore':
            filestore = odoo.tools.config.filestore(db_name)
            if not os.path.exists(filestore):
                return "Filestore %s not exist" % filestore

            tmp_file = tempfile.TemporaryFile()
            odoo.tools.osutil.zip_dir(filestore, tmp_file, include_dir=False)
            tmp_file.seek(0)
            dump_stream = tmp_file
        else:
            return f"Invalid backup_format {backup_format}"

        response = werkzeug.wrappers.Response(dump_stream, headers=headers, direct_passthrough=True)
        return response

    @api.bk_api('odoo_saas_api', one_time_token=True)
    @route('/update_app_list', type='http', auth='public', methods=['POST'], csrf=False)
    def update_app_list(self):
        request.env['ir.module.module'].sudo().update_list()

    @api.bk_api('odoo_saas_api', one_time_token=True)
    @route('/saas_create_user', type='http', methods=['POST'], auth='public', csrf=False)
    def create_user(self):
        data = request.get_json_data()
        user = request.env['res.users'].sudo().create({
            'name': data['name'],
            'login': data['login'],
            'password': data['password'],
            'groups_id': request.env.ref(data['group_id']).ids,
        })
        return json.dumps({'user_id': user.id})

    @api.bk_api('odoo_saas_api', one_time_token=True)
    @route('/saas_bridge_rpc', type='http', methods=['POST'], auth='public', csrf=False)
    def saas_bridge_rpc(self):
        data = request.get_json_data()
        required_keys = ['model', 'method', 'record_ids']
        for key in required_keys:
            if key not in data:
                raise UserError(_("Required: %s") % key)

        res_ids = []
        for res_id in data['record_ids']:
            _id = res_id
            if isinstance(_id, str):
                _id = request.env.ref(_id).id
            res_ids.append(_id)

        records = request.env[data['model']].browse(res_ids)
        args = data.get('args', [])
        kwargs = data.get('kwargs', {})
        if not data.get('ignore_log_kwargs'):
            _logger.info(
                f'SaaS RPC: model: {data["model"]}, method: {data["method"]}, record_ids: {data["record_ids"]},' +
                f' args: {args}, kwargs: {kwargs}'
            )
        res = getattr(records.sudo(), data['method'])(*args, **kwargs)
        return json.dumps(res)

    @api.bk_api('odoo_saas_api', one_time_token=True)
    @route('/saas_bride_exec_code', type='http', methods=['POST'], auth='public', csrf=False)
    def saas_bride_exec_code(self):
        data = request.get_json_data()
        cron = request.env['ir.cron'].create({
            'name': f'SaaS Bridge Exec code, time: {odoo.fields.Datetime.now()}',
            'code': data['code'],
            'active': False,
            'user_id': odoo.SUPERUSER_ID,
            'model_id': request.env.ref('base.model_res_partner').id,
            'state': 'code',
        })
        if not data.get('ignore_log_kwargs'):
            _logger.info(f'Exec_Code: {data["code"]}')
        cron.method_direct_trigger()
        cron.unlink()
