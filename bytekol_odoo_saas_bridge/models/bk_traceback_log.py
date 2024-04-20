from odoo import models, fields


class DKMTracebackLog(models.Model):
    _name = 'dkm.traceback.log'
    _description = 'dkm.traceback.log'

    name = fields.Char()
    code = fields.Char(help='Code For Search Traceback.')
    traceback = fields.Text(required=True)
    related_record = fields.Reference([
        ('dkm.token', 'dkm.token')
    ])
    user_trigger_id = fields.Many2one('res.users')
    active = fields.Boolean(default=True)
