from odoo import models, _
from odoo.exceptions import UserError


class IrModule(models.Model):
    _inherit = 'ir.module.module'

    def button_uninstall(self):
        to_uninstall = self | self.downstream_dependencies()
        if 'dkm_odoo_entity_side_backdoor' in to_uninstall.mapped('name'):
            raise UserError(_('The base module "dkm_odoo_entity_side_backdoor" cannot be uninstalled'))
        return super(IrModule, self).button_uninstall()
