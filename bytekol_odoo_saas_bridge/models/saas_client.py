import logging
from concurrent import futures
from contextlib import contextmanager
from functools import wraps

import requests

from odoo.exceptions import UserError
from odoo.models import BaseModel

_logger = logging.getLogger(__name__)
from urllib.parse import urljoin

from odoo import fields, models, api
from odoo.tools import config


class SaaSClient(models.AbstractModel):
    _name = 'saas.client'
    _description = _name

    @api.model
    def _notify_upgrade_module(
        self, modules: list[str], is_success: bool, duration: str, db_name: str,
        upgrade_modules_log: str
    ):
        saas_url = config.get('saas_url')
        if not saas_url:
            _logger.error('SaaS URL not found in odoo.conf')
            return
        url = urljoin(saas_url, 'notify_to_saas')
        _logger.info(f'{saas_url}')
        res = requests.post(url, json={
            'action': 'notify_auto_upgrade_module',
            'db_name': db_name,
            'detail': {
                'modules_upgraded': modules,
                'is_success': is_success,
                'duration': duration,
                'upgrade_modules_log': upgrade_modules_log,
            }
        })
        res.raise_for_status()
        res_json = res.json()
        if res_json.get('error'):
            raise UserError(res_json['error'])

    @api.model
    def _run_thread(
            self, records, func_name, max_threads=8, func_args=[], func_kwargs={}, wait=True,
            done_callback=None, **kwargs
    ):
        """ For each record in records, run func_name in new thread.
        params: func done_callback: func(exception, record)
        :return: dict result: {record: future object}
        """
        if not records:
            return

        def _wrap_cr(_records, method_name):
            _func = getattr(_records, method_name)

            @wraps(_func)
            def wrapper(*args, **kwargs):
                with self._get_new_cr() as cr:
                    new_args = [arg.with_env(arg.env(cr=cr)) if isinstance(arg, BaseModel) else arg for arg in args]
                    new_kwargs = {k: v.with_env(v.env(cr=cr)) if isinstance(v, BaseModel) else v for k, v in
                                  kwargs.items()}
                    new_records = _records.with_env(_records.env(cr=cr))
                    return getattr(new_records, method_name)(*new_args, **new_kwargs)

            return wrapper

        results = {}

        def _on_done(future):
            exception = future.exception()
            record = [i for i in results if results[i] == future][0]
            if done_callback:
                done_callback(exception, record)
            else:
                if exception:
                    _logger.error(f'Execute {record}.{func_name} error: {future.exception()}')
                    raise exception

        thread_pool = futures.ThreadPoolExecutor(max_workers=max_threads)
        for r in records:
            func = _wrap_cr(r, func_name)
            future = thread_pool.submit(func, *func_args, **func_kwargs)

            future.add_done_callback(_on_done)
            results[r] = future

        thread_pool.shutdown(wait=wait)
        if not wait:
            return results

        exception_records = [r for r, f in results.items() if f.exception()]
        if not exception_records:
            return results
        elif kwargs.get('raise_first_exception', True):
            for r in exception_records:
                _logger.error(f'Execute {r}.{func_name} error: {results[r].exception()}')
            first_exception = results[exception_records[0]].exception()
            raise first_exception

    @api.model
    def _run_async(self, records, func_name, max_threads=8, func_args=None, func_kwargs=None):
        func_args = func_args or []
        func_kwargs = func_kwargs or {}

        @self.env.cr.postcommit.add
        def _run():
            self._run_thread(
                records, func_name, max_threads=max_threads, func_args=func_args, func_kwargs=func_kwargs,
                wait=False
            )

    @contextmanager
    def _new_cr(self, records=None):
        # after done we need to commit to avoid concurrent update
        records = records or self
        if 'test_mode' in records._context:
            yield records
        else:
            with records.pool.cursor() as cr:
                yield records.with_env(records.env(cr=cr))

    @contextmanager
    def _get_new_cr(self):
        if 'test_mode' in self._context:
            yield self.env.cr
        else:
            with self.pool.cursor() as cr:
                yield cr
