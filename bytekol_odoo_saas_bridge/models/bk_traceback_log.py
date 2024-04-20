from odoo import models, fields


class BKTracebackLog(models.Model):
    _name = 'bk.traceback.log'
    _description = 'bk.traceback.log'

    name = fields.Char()
    code = fields.Char(help='Code For Search Traceback.')
    traceback = fields.Text(required=True)
    related_record = fields.Reference([
        ('bk.token', 'bk.token')
    ])
    user_trigger_id = fields.Many2one('res.users')
    active = fields.Boolean(default=True)
