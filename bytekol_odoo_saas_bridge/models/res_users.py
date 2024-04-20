from odoo import api, fields, models, _
from odoo.addons.bytekol_odoo_saas_bridge.exceptions import OdooSaaSClientResourceException
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self).create(vals_list)
        internal_user = users.filtered(lambda u: not u.share)
        client_data = self.env['odoo.saas.client.data']
        if internal_user and client_data.plan_id and client_data.is_user_pricing \
                and self.get_internal_user_count() > client_data.max_internal_user:
            message = _(
                'You cannot create more than the number of internal '
                'users you have purchased.<br>'
                'If you are administrator, go to this link to buy more users:<br>'
                '<a href="%s" target="_new">Buy more users</a>'
                % client_data.odoo_entity_dashboard_link
            )
            raise OdooSaaSClientResourceException(message)
        return users

    @api.model
    def get_internal_user_count(self):
        return self.sudo().search_count([('share', '=', False), ('active', '=', True)])
