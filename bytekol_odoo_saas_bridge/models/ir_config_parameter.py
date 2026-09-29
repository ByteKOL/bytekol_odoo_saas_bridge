from odoo import api, models


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def set_param(self, key, value):
        # Odoo 20 renamed set_param -> set_str; keep alias for SaaS RPC callers.
        return self.set_str(key, value)

    @api.model
    def get_param(self, key, default=False):
        # Odoo 20 renamed get_param -> get_str; keep alias for SaaS RPC callers.
        return self.get_str(key, default)
