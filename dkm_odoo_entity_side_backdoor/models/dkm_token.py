import uuid
from datetime import timedelta

from odoo import models, fields, api, SUPERUSER_ID
from odoo.addons.dkm_odoo_entity_side_backdoor.api import TokenException


class DkmToken(models.Model):
    _name = 'dkm.token'
    _description = 'dkm Token'
    _mail_post_access = 'read'
    _order = 'id desc'

    name = fields.Char(required=True)
    token = fields.Char(required=True, readonly=True, default=uuid.uuid4())
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    live_time = fields.Float(help="Live time (seconds) since creation date of token, "
                                  "If value <= 0 then effect is permanent.", default=0)
    is_expire = fields.Boolean(compute='_compute_is_expire', search='_search_is_expire',
                               help="Compute field depend on fields.Datetime.now(), only use in view")
    is_permanent = fields.Boolean(compute='_compute_date_expire_and_is_permanent', compute_sudo=True)
    date_expire = fields.Datetime(compute='_compute_date_expire_and_is_permanent', compute_sudo=True,
                                  inverse='_inverse_date_expire')
    description = fields.Html()
    active = fields.Boolean(default=True)
    purpose = fields.Char(help='Purpose of this token', default='api_general')
    clean_type = fields.Selection([
        ('no', 'No'),
        ('clean_when_expired', 'Clean when expired')
    ], default='clean_when_expired')

    def _compute_is_expire(self):
        for r in self:
            r.is_expire = r._is_expire()

    @api.depends('live_time', 'create_date')
    def _compute_date_expire_and_is_permanent(self):
        for r in self:
            if r.live_time <= 0:
                r.date_expire = False
                r.is_permanent = True
            else:
                r.is_permanent = False
                r.date_expire = r.create_date + timedelta(seconds=r.live_time)

    @api.model
    def _search_is_expire(self, operator, value):
        assert operator in ['=', '!=', '<>']
        if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
            search_operator = 'in'
        else:
            search_operator = 'not in'
        tokens_expire = []
        for token in self.search([]):
            if token.is_expire:
                tokens_expire.append(token.id)
        return [('id', search_operator, tokens_expire)]

    def _inverse_date_expire(self):
        for r in self:
            if r.date_expire:
                r.live_time = (r.date_expire - r.create_date).total_seconds()
            else:
                r.live_time = 0

    def _is_expire(self):
        self.ensure_one()
        if self.live_time <= 0:
            return False
        return self.date_expire < fields.Datetime.now()

    @api.model
    def is_token_valid(self, token, purpose):
        """
        :param token:
        :param purpose:
        :return:
        """
        token_exist = self.search([
            ('token', '=', token),
            ('purpose', '=', purpose)
        ], limit=1).filtered(lambda t: not t._is_expire())

        if token_exist:
            return token_exist
        return False

    @api.model
    def ensure_token_valid(self, token, purpose):
        """
        :param str token:
        :param str purpose:
        :return:
        """
        token = self.is_token_valid(token, purpose)
        if not token:
            raise TokenException("Token Invalid.")
        return token

    @api.model
    def _cron_clean_dkm_token(self):
        tokens_to_unlink = self.search([
            ('clean_type', '=', 'clean_when_expired')
        ]).filtered(lambda t: t._is_expire())
        tokens_to_unlink.unlink()

    @api.model
    def _self_inject_token_for_verify_request(self, live_time=20):
        return self.create({
            'name': 'token for verify request',
            'user_id': SUPERUSER_ID,
            'purpose': 'verify_request',
            'live_time': live_time
        })
