import time
import uuid

import werkzeug
import os
import json
import logging

_logger = logging.getLogger(__name__)

import odoo
from odoo.modules.registry import Registry
from odoo.service import db
from odoo.tools import config
from odoo.http import request, route, Controller

from .. import utils

saas_datadir = os.path.join(config.get('data_dir'), 'saas_data')


class AutoUpgradeController(Controller):

    @route('/check_and_upgrade_module', methods=['GET'], auth='none')
    def check_and_upgrade_modules(self):
        env = None
        msg_done = 'check_and_upgrade_module_done'
        if config.get('disable_auto_upgrade_modules'):
            _logger.info(
                f'Do not automatically upgrade modules because odoo config: disable_auto_upgrade_modules=True.\n'
                f'{msg_done}'
            )
            return
        if not os.path.exists(saas_datadir):
            _logger.info(f'saas_datadir: {saas_datadir} does not exist, ignore auto upgrade module.\n'
                         f'{msg_done}')
            return
        # saas_url = config.get('saas_url')
        # saas_container_id = config.get('saas_container_id')

        option_skip_auto_upgrade_module_file_path = '/tmp/skip_auto_upgrade_module'
        if os.path.exists(option_skip_auto_upgrade_module_file_path):
            _logger.info(f'Skip auto-upgrade modules, because file: {option_skip_auto_upgrade_module_file_path} is existed.')
            os.remove(option_skip_auto_upgrade_module_file_path)
            _logger.info(msg_done)
            return

        host_url = request.httprequest.host_url.strip()
        if not host_url.startswith('http://localhost'):
            raise werkzeug.exceptions.Forbidden()

        dbs = db.list_dbs(force=True)
        available_dbs = set(dbs) - set(db.list_db_incompatible(dbs))

        modules_changed_set = set()
        file_to_delete = set()
        for file in os.listdir(saas_datadir):
            full_path = os.path.join(saas_datadir, file)
            if os.path.isfile(full_path) and file.startswith('modules_changed'):
                file_to_delete.add(full_path)
                with open(full_path, 'r') as f:
                    modules_list = json.loads(f.read())
                    modules_changed_set.update(modules_list)

        if not modules_changed_set:
            _logger.info(f'No modules changed found, skip upgrading odoo modules.')
            _logger.info(msg_done)
            return

        for dbname in available_dbs:
            start_time = time.time()
            registry = Registry(dbname)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'active_test': False})
                head_log_code = uuid.uuid4().hex
                try:
                    odoo_modules = env['ir.module.module'].search([
                        ('state', '=', 'installed'),
                        ('name', 'in', list(modules_changed_set))
                    ])
                    if odoo_modules:
                        _logger.info(f'Starting upgrade modules on database: {dbname}.\n'+
                                     f'Modules to auto upgrade: {odoo_modules.mapped("name")} | {head_log_code}')
                        odoo_modules.with_context(prefetch_fields=False).button_immediate_upgrade()
                    else:
                        msg = f'No module found to upgrade for db: {dbname}'
                        _logger.info(msg)
                        continue
                except Exception as e:
                    _logger.error(str(e), exc_info=e)
                    if env:
                        env.cr.rollback()

                duration = utils.format_duration_time(start_time, time.time())
                tail_log_code = uuid.uuid4().hex
                _logger.info(f'Auto-upgraded modules on database {dbname} done, duration: {duration} | {tail_log_code}\n'+
                             f'--------------------------------------------------------------------')
                # don't need to notify anymore, because saas already view logs when restarting.
        for file in file_to_delete:
            os.remove(file)
        _logger.info(msg_done)
