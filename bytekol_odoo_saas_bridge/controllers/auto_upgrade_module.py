import time

import werkzeug
import os
import json
import logging

_logger = logging.getLogger(__name__)

import odoo
from odoo.modules.registry import Registry
from odoo.service import db
from odoo.tools import config, format_duration
from odoo.http import request, route, Controller
saas_datadir = os.path.join(config.get('data_dir'), 'saas_data')

class AutoUpgradeController(Controller):

    @route('/check_and_upgrade_module', methods=['GET'], auth='none')
    def check_and_upgrade_modules(self):
        env = None
        if config.get('disable_auto_upgrade_modules'):
            _logger.info(
                f'Do not automatically upgrade modules because odoo config: disable_auto_upgrade_modules=True'
            )
            return
        if not os.path.exists(saas_datadir):
            _logger.info(f'saas_datadir: {saas_datadir} does not exist, ignore auto upgrade module')
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

        for dbname in available_dbs:
            start = time.time()
            is_success = True
            odoo_modules_name = []
            registry = Registry(dbname)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'active_test': False})
                try:
                    odoo_modules = env['ir.module.module'].search([
                        ('state', '=', 'installed'),
                        ('name', 'in', list(modules_changed_set))
                    ])
                    odoo_modules_name = odoo_modules.mapped('name')
                    if odoo_modules:
                        _logger.info(f'Modules to auto upgrade: {odoo_modules.mapped("name")}')
                        odoo_modules.with_context(prefetch_fields=False).button_immediate_upgrade()
                        print(f'Upgraded Modules: {odoo_modules.mapped('name')}')
                    else:
                        msg = f'No module found to upgrade for db: {dbname}'
                        _logger.info(msg)
                        print(msg)
                        continue
                except Exception as e:
                    is_success = False
                    _logger.error(str(e), exc_info=e)
                    if env:
                        env.cr.rollback()

                duration = format_duration(time.time() - start)
                self._notify_auto_upgrade_modules(
                    env, odoo_modules_name, is_success, dbname, duration
                )
        for file in file_to_delete:
            os.remove(file)

    def _notify_auto_upgrade_modules(
        self, env, module_upgrade: list[str], is_success: bool, db_name: str, duration: str
    ):
        if not config.get('saas_url'):
            return
        queue = env['simple.queue.job']._create_job({
            'name': 'Notify Auto Upgrade Modules Status',
            'model': 'saas.client',
            'method': '_notify_upgrade_module',
            'method_args': [module_upgrade, is_success, duration, db_name],
        })
        queue._thread_execute_job()
