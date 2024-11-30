from odoo import models


class OdooSaaSClientData(models.AbstractModel):
    _inherit = 'odoo.saas.client.data'

    @property
    def max_websites(self):
        return self.get_client_data_dict().get('max_websites')
