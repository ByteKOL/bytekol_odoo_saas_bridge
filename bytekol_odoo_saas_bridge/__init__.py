from . import models
from . import controllers


import odoo
import logging
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
        thread_type = getattr(thread, 'type', None)
        if not thread.daemon and thread_type != 'websocket' or thread_type == 'cron':
            # We apply the limits on cron threads and HTTP requests,
            # websocket requests excluded.
            if getattr(thread, 'start_time', None):
                thread_execution_time = time.time() - thread.start_time
                thread_limit_time_real = config['limit_time_real']
                if (getattr(thread, 'type', None) == 'cron' and
                        config['limit_time_real_cron'] and config['limit_time_real_cron'] > 0):
                    thread_limit_time_real = config['limit_time_real_cron']
                if thread_limit_time_real and thread_execution_time > thread_limit_time_real:
                    _logger.warning(
                        'Thread %s virtual real time limit (%d/%ds) reached.',
                        thread, thread_execution_time, thread_limit_time_real)

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
