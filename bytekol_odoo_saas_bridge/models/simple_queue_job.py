import json
import traceback
from contextlib import contextmanager

from odoo import models, fields, api


class SimpleQueueJob(models.Model):
    _name = 'simple.queue.job'
    _order = 'id desc'
    _description = 'Simple Queue Job'

    name = fields.Char(string='Queue Name')
    model = fields.Char(required=True)
    method = fields.Char(required=True)
    res_ids_json = fields.Char(default='[]')
    args_json = fields.Char(default='[]')
    kwargs_json = fields.Char(default='{}')
    context_json = fields.Char(default='{}')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ], default='queued', readonly=True, string='State')
    total_retries = fields.Integer(default=3)
    retry_count = fields.Integer()
    error_txt = fields.Text(readonly=True)

    @api.model
    def _create_job(self, data):
        with self._new_cr() as self:
            record = self.env['simple.queue.job'].sudo().create({
                'name': data['name'],
                'model': data['model'],
                'method': data['method'],
                'res_ids_json': str(data.get('res_ids', [])),
                'args_json': json.dumps(data.get('method_args', [])),
                'kwargs_json': json.dumps(data.get('method_kwargs', {})),
                'context_json': json.dumps(data.get('context', {})),
                'state': 'queued',
                'total_retries': data.get('total_retries', 3),
            })
            self.cr_commit(self.env.cr)
            return record

    def _execute_job(self):
        if self.res_ids_json:
            res_ids = json.loads(self.res_ids_json)
            records = self.env[self.model].browse(res_ids)
        else:
            records = self.env[self.model]
        context = json.loads(self.context_json)
        args = json.loads(self.args_json)
        kwargs = json.loads(self.kwargs_json)
        with self.env.cr.savepoint():
            try:
                getattr(records.with_context(**context), self.method)(*args, **kwargs)
            except Exception as e:
                with self._new_cr() as self:
                    self.write({'state': 'failed', 'error_txt': traceback.format_exc()})
                raise
            else:
                self.state = 'done'

    def _thread_execute_job(self):
        self.ensure_one()
        self.env['saas.client']._run_thread(self, '_execute_job')

    def action_execute(self):
        self.ensure_one()
        self._execute_job()

    @api.model
    def _cron_retry_queue_jobs(self):
        failed_job = self.env['simple.queue.job'].search([
            ('state', '=', 'failed'),
        ])
        for job in failed_job.filtered(lambda j: j.retry_count < j.total_retries):
            try:
                with self.env.cr.savepoint():
                    job._execute_job()
            except Exception as e:
                pass
            finally:
                with job._new_cr() as new_job:
                    new_job.retry_count += 1

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

    @api.model
    def cr_commit(self, cr):
        context = self._context
        if 'test_mode' in context or 'ignore_auto_commit' in context:
            return
        cr.commit()
