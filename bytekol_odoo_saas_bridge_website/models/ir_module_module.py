from odoo import models, _
from odoo.exceptions import UserError


class IrModule(models.Model):
    _inherit = 'ir.module.module'

    def button_uninstall(self):
        to_uninstall = self | self.downstream_dependencies()
        to_uninstall_module_names = to_uninstall.mapped('name')
        if 'bytekol_odoo_saas_bridge_website' in to_uninstall_module_names and 'website' not in to_uninstall_module_names:
            raise UserError(_('You are using the website and cannot uninstall: bytekol_odoo_saas_bridge_website'))
        return super(IrModule, self).button_uninstall()

