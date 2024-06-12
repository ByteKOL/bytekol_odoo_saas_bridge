from odoo import models, _
from odoo.addons.bytekol_odoo_saas_bridge.exceptions import OdooSaaSClientResourceException
from odoo.exceptions import UserError
from markupsafe import Markup


class IrModule(models.Model):
    _inherit = 'ir.module.module'

    def button_uninstall(self):
        to_uninstall = self | self.downstream_dependencies()
        if 'bytekol_odoo_saas_bridge' in to_uninstall.mapped('name'):
            raise UserError(_('The module "bytekol_odoo_saas_bridge" cannot be uninstalled'))
        return super(IrModule, self).button_uninstall()

    def button_immediate_install(self):
        if not self.env['odoo.saas.client.data'].plan_id:
            return super(IrModule, self).button_immediate_install()

        old_cr = self.env.cr
        with self.pool.cursor() as cr:
            self = self.with_env(self.env(cr=cr))
            # domain to select auto-installable (but not yet installed) modules
            auto_domain = [('state', '=', 'uninstalled'), ('auto_install', '=', True)]

            # determine whether an auto-install module must be installed:
            #  - all its dependencies are installed or to be installed,
            #  - at least one dependency is 'to install'
            install_states = frozenset(('installed', 'to install', 'to upgrade'))

            def must_install(module):
                states = {dep.state for dep in module.dependencies_id if dep.auto_install_required}
                return states <= install_states and 'to install' in states

            modules = self
            while modules:
                # Mark the given modules and their dependencies to be installed.
                modules._state_update('to install', ['uninstalled'])

                # Determine which auto-installable modules must be installed.
                modules = self.search(auto_domain).filtered(must_install)

            to_install = self.search([('state', 'in', ['to install'])])
            to_install_modules_name = to_install.mapped('name')
            client_data = self.env['odoo.saas.client.data']
            for banned_module in client_data.exclusion_module_name:
                if banned_module.strip() in to_install_modules_name:
                    message = _(
                        'The "%s" plan you are using does not allow installation of module %s, '
                        'please upgrade to another plan to be able to install it.<br>'
                        'Details of plans can be found here: <br>'
                        '<a href="%s" target="_blank">%s</a>'
                        % (client_data.plan_name, banned_module, client_data.pricing_url, client_data.pricing_url)
                    )
                    raise OdooSaaSClientResourceException(Markup(message))

            allow_module_names = client_data.allow_module_names
            if allow_module_names:
                for to_install_module_name in to_install.filtered(lambda m: m.application).mapped('name'):
                    if to_install_module_name not in allow_module_names:
                        message = _(
                            "You cannot install additional odoo modules, please purchase additional"
                            " odoo modules or contact your service provider"
                        )
                        raise OdooSaaSClientResourceException(Markup(message))

            cr.rollback()
        self = self.with_env(self.env(cr=old_cr))
        return super(IrModule, self).button_immediate_install()
