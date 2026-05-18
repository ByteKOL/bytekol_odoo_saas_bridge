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
from ..utils import Ansi

saas_datadir = os.path.join(config.get('data_dir'), 'saas_data')


class AutoUpgradeController(Controller):

    def _upgrade_modules_blocking_cron(self, odoo_modules, dbname: str, head_log_code: str) -> None:
        lock_timeout_seconds = int(config.get('auto_upgrade_modules_lock_timeout_seconds', 180))
        lock_timeout_ms = max(1, lock_timeout_seconds) * 1000
        current_cr = odoo_modules.env.cr
        # Hold ir_cron row lock in this transaction so no cron can run during module upgrade.
        current_cr.execute("SET LOCAL lock_timeout = %s", [f"{lock_timeout_ms}ms"])
        current_cr.execute("SELECT * FROM ir_cron FOR UPDATE")
        _logger.info(
            f'[{head_log_code}] DB {dbname}: acquired ir_cron lock, start module upgrade with cron blocked.'
        )
        odoo_modules.with_context(prefetch_fields=False).button_immediate_upgrade()

    @route('/check_and_upgrade_module', methods=['GET'], auth='none')
    def check_and_upgrade_modules(self):
        env = None
        msg_done = 'check_and_upgrade_module_done'
        if config.get('disable_auto_upgrade_modules'):
            _logger.info(
                f'{Ansi.title_sky_blue("Do not automatically upgrade modules because odoo config")}: '
                f'disable_auto_upgrade_modules=True.\n'
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
        if not host_url.startswith('http://127.0.0.1'):
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
            _logger.info(Ansi.title_hot_pink(f'No modules changed found, skip upgrading odoo modules.'))
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
                        _logger.info(f'{Ansi.title_sky_blue("Starting upgrade modules on database")}: '
                                     f'{Ansi.title_violet(dbname)}\n' +
                                     f'Modules to auto upgrade: {odoo_modules.mapped("name")} | {head_log_code}')
                        self._upgrade_modules_blocking_cron(odoo_modules, dbname, head_log_code)
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
                _logger.info(
                    Ansi.title_hot_pink(f'Auto-upgraded modules on database {dbname} done, '
                                              f'duration: {duration} | {tail_log_code}\n') +
                    f'--------------------------------------------------------------------'
                )
                # don't need to notify anymore, because saas already view logs when restarting.
        for file in file_to_delete:
            os.remove(file)
        _logger.info(msg_done)
