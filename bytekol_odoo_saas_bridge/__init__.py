import os
import json
import logging
import requests
import time

from . import models
from . import controllers


import odoo
from odoo.tools import config
from odoo import fields

from odoo.addons.bytekol_odoo_saas_bridge.utils import Ansi


saas_datadir = os.path.join(config.get('data_dir'), 'saas_data')
if not os.path.exists(saas_datadir):
    os.mkdir(saas_datadir)

_logger = logging.getLogger(__name__)

if 'bytekol_odoo_saas_bridge' not in odoo.tools.config.get('server_wide_modules', '').split(','):
    _logger.error('module bytekol_odoo_saas_bridge must be loaded in server_wide_modules')

from odoo.service.server import ThreadedServer


origin = ThreadedServer.process_limit


def process_limit_patch(self):
    from odoo.service.server import memory_info
    import psutil
    import os
    from odoo.tools import config
    import threading
    import time
    from .custom_config import custom_config

    memory = memory_info(psutil.Process(os.getpid()))
    if config['limit_memory_soft'] and memory > config['limit_memory_soft']:
        _logger.warning('Server memory limit (%s) reached.', memory)
        self.limits_reached_threads.add(threading.current_thread())

    for thread in threading.enumerate():
        if not thread.daemon or getattr(thread, 'type', None) == 'cron':
            # We apply the limits on cron threads and HTTP requests,
            # longpolling requests excluded.
            if getattr(thread, 'start_time', None):
                thread_execution_time = time.time() - thread.start_time
                thread_limit_time_real = config['limit_time_real']
                if (getattr(thread, 'type', None) == 'cron' and
                        config['limit_time_real_cron'] and config['limit_time_real_cron'] > 0):
                    thread_limit_time_real = config['limit_time_real_cron']
                if thread_limit_time_real and thread_execution_time > thread_limit_time_real:
                    _logger.warning(
                        'Thread %s virtual real time limit (%d/%ds) reached. req_path: %s',
                        thread, thread_execution_time, thread_limit_time_real, getattr(thread, '_req_path', None))

                    saas_url = custom_config.get('options', 'saas_url', fallback=None)
                    if saas_url:
                        import uuid
                        error_log_code = uuid.uuid4().hex
                        _logger.error(f'thread_limit_time_real_code: {error_log_code}')
                        import requests
                        try:
                            requests.post(f'{saas_url}/container_thread_limit_time_real_handler', json={
                                'admin_password': config.get("admin_passwd"),
                                'saas_container_id': custom_config.get('options', 'saas_container_id', fallback=None),
                                'error_log_code': error_log_code,
                                'thread_execution_time': thread_execution_time,
                                'thread_limit_time_real': thread_limit_time_real
                            }, verify=False)
                        except Exception as e:
                            _logger.error('request: container_thread_limit_time_real_handler failed:')
                            _logger.error(str(e))

                    self.limits_reached_threads.add(thread)
    # Clean-up threads that are no longer alive
    # e.g. threads that exceeded their real time,
    # but which finished before the server could restart.
    for thread in list(self.limits_reached_threads):
        if not thread.is_alive():
            self.limits_reached_threads.remove(thread)
    if self.limits_reached_threads:
        self.limit_reached_time = self.limit_reached_time or time.time()
    else:
        self.limit_reached_time = None

ThreadedServer.process_limit = process_limit_patch


def _scan_modules_file_change():
    import time
    import hashlib

    def _is_odoo_module(path):
        if not os.path.isdir(path):
            return False
        manifest_path = os.path.join(path, '__manifest__.py')
        old_manifest_path = os.path.join(path, '__openerp__.py')
        return os.path.isfile(manifest_path) or os.path.isfile(old_manifest_path)

    def _get_checksum_directory_metadata(path, hash_algo='sha256'):
        h = hashlib.new(hash_algo)
        for root, dirs, files in sorted(os.walk(path)):
            for fname in sorted(files):
                file_path = os.path.join(root, fname)
                rel_path = os.path.relpath(file_path, path).replace(os.sep, '/')
                try:
                    stat = os.stat(file_path)
                    h.update(rel_path.encode('utf-8'))
                    h.update(str(stat.st_mtime).encode('utf-8'))
                    h.update(str(stat.st_size).encode('utf-8'))
                except Exception as e:
                    continue
        return h.hexdigest()

    addon_paths = [dir_path for dir_path in config.get('addons_path').split(',') if dir_path]
    module_check_sum = dict()

    for dir_path in addon_paths:
        for root, dirs, files in os.walk(dir_path):
            for dir_name in dirs:
                full_dir_path = os.path.join(root, dir_name)
                if not _is_odoo_module(full_dir_path):
                    continue
                if dir_name not in module_check_sum:
                    module_check_sum[dir_name] = _get_checksum_directory_metadata(full_dir_path)

    modules_changed = []

    check_sum_addon_path_file_path = os.path.join(saas_datadir, 'checksum_addon_path.json')
    if os.path.isfile(check_sum_addon_path_file_path):
        with open(check_sum_addon_path_file_path, 'r') as f:
            checksum_file_txt = f.read()

    if not os.path.exists(check_sum_addon_path_file_path) or not checksum_file_txt.strip():
        data_to_push = {}
        for module_name, checksum in module_check_sum.items():
            data_to_push[module_name] = {
                'last_checksum': checksum,
            }
        with open(check_sum_addon_path_file_path, 'w') as f:
            f.write(json.dumps(data_to_push))
    else:
        checksum_file_data = json.loads(checksum_file_txt)
        for module_name, current_checksum in module_check_sum.items():
            if module_name in checksum_file_data:
                if checksum_file_data[module_name]['last_checksum'] != current_checksum:
                    modules_changed.append(module_name)
            else:
                checksum_file_data[module_name] = {}
            checksum_file_data[module_name]['last_checksum'] = current_checksum

        with open(check_sum_addon_path_file_path, 'w') as f:
            f.write(json.dumps(checksum_file_data))

        if modules_changed:
            now_str = fields.Datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            modules_changed_file_path = os.path.join(saas_datadir, f'modules_changed_{now_str}.json')
            with open(modules_changed_file_path, 'w') as f:
                f.write(json.dumps(modules_changed))
            _logger.info(
                f'Found {len(modules_changed)} modules has changed the source code: \n'
                f'{modules_changed}'
            )
        else:
            _logger.info('No modules have been found to have changed the source code')


def _check_and_upgrade_modules():
    if not config['http_enable']:
        _logger.info(Ansi.title_hot_pink('http is not enable, ignore auto _check_and_upgrade_modules'))
        return
    time.sleep(1)
    try:
        url = f'http://127.0.0.1:{config.get("http_port")}/check_and_upgrade_module'
        res = requests.get(url, verify=False)
    except Exception as e:
        _logger.error(f'Cannot call check_and_upgrade_module, detail: {str(e)}')

def _thread_check_and_upgrade_modules():
    import threading
    t = threading.Thread(target=_check_and_upgrade_modules)
    t.start()

_scan_modules_file_change()
_thread_check_and_upgrade_modules()
