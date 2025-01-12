from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        client_data = self.env['odoo.saas.client.data'].get_client_data_dict()
        result['odoo_saas_client_data'] = client_data
        return result
