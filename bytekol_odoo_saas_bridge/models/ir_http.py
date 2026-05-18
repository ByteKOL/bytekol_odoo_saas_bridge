from odoo import models
import threading
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        client_data = self.env['odoo.saas.client.data'].get_client_data_dict()
        result['odoo_saas_client_data'] = client_data
        return result

    @classmethod
    def _pre_dispatch(cls, rule, args):
        super()._pre_dispatch(rule, args)
        req_path = request.httprequest.path
        threading.current_thread()._req_path = req_path
