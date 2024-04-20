from odoo import api, models, fields, _
from odoo.addons.bytekol_odoo_saas_bridge.exceptions import OdooSaaSClientResourceException
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ResCompany, self).create(vals_list)
        client_data = self.env['odoo.saas.client.data']
        if client_data.plan_id and not client_data.allow_multiple_company and self.search_count([]) > 1:
            message = _(
                "The '%s' plan you are using does not allow multi-company features, " 
                "please upgrade to another plan to create a new company. <br/>"
                "Details of plans can be found here: <br/>"
                '<a href="%s" target="_blank">%s</a>' % (client_data.plan_name, client_data.pricing_url, client_data.pricing_url)
            )
            raise OdooSaaSClientResourceException(message)
        return records
