from markupsafe import Markup

from odoo import models, api, _
from odoo.addons.bytekol_odoo_saas_bridge.exceptions import OdooSaaSClientResourceException


class Website(models.Model):
    _inherit = 'website'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        max_website = self.env['odoo.saas.client.data'].max_websites
        if max_website and self._get_current_website_count() > max_website:
            message = _(
                'You have reached the maximum number of websites you can create, if you want to create more, '
                'you may need to upgrade to a new plan, detail: <a href="%s" target="_new">Pricing Plan</a>, '
                'please contact your service provider for more details.'
            ) % self.env['odoo.saas.client.data'].pricing_url
            raise OdooSaaSClientResourceException(Markup(message))
        return records

    @api.model
    def _get_current_website_count(self):
        return self.with_context(active_test=False).sudo().search_count([])
