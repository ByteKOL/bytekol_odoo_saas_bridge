import os.path
import traceback

import json
import logging
from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class OdooSaaSClientData(models.AbstractModel):
    _name = 'odoo.saas.client.data'
    _description = _name

    id = fields.Integer('ID', readonly=True)
    key = fields.Char()
    value = fields.Text()

    @api.model
    def get_client_data_dict(self):
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_catalog.pg_class
                WHERE relname = 'odoo_saas_client_data'
                AND relkind = 'r'
            ) AS table_existence;
            """)
        if self.env.cr.fetchone()[0]:
            self.env.cr.execute("select value from odoo_saas_client_data where key = 'odoo_saas_client_file';")
            file_path = self.env.cr.fetchone()[0]
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.loads(f.read())
            else:
                _logger.error(f'get_client_data_dict failed, file: {file_path} does not exist')
        else:
            _logger.error('get_client_data_dict failed, table odoo_saas_client_data does not exist')
        return {}

    @property
    def max_internal_user(self):
        return self.get_client_data_dict().get('max_internal_user')

    @property
    def odoo_entity_id(self):
        return self.get_client_data_dict().get('id')

    @property
    def is_user_pricing(self):
        return self.get_client_data_dict().get('is_user_pricing')

    @property
    def subscription_id(self):
        return self.get_client_data_dict().get('subscription_id')

    @property
    def plan_id(self):
        return self.get_client_data_dict().get('plan_id')

    @property
    def plan_name(self):
        return self.get_client_data_dict().get('plan_name')

    @property
    def allow_multiple_company(self):
        return self.get_client_data_dict().get('allow_multiple_company')

    @property
    def allow_custom_addon(self):
        return self.get_client_data_dict().get('allow_custom_addon')

    @property
    def allow_download_backup(self):
        return self.get_client_data_dict().get('allow_download_backup')

    @property
    def exclusion_module_name(self):
        return self.get_client_data_dict().get('exclusion_module_name')

    @property
    def is_saas_plan_trial(self):
        return self.get_client_data_dict().get('is_saas_plan_trial')

    @property
    def default_trial_days(self):
        return self.get_client_data_dict().get('default_trial_days')

    @property
    def can_create_new_internal_user(self):
        return self.get_client_data_dict().get('can_create_new_internal_user')

    @property
    def odoo_entity_dashboard_link(self):
        return self.get_client_data_dict().get('odoo_entity_dashboard_link')

    @property
    def pricing_url(self):
        return self.get_client_data_dict().get('pricing_url')

    @api.model
    def open_dialog_message(self, html):
        return {
            'type': 'ir.actions.client',
            'tag': 'client_action_open_dialog',
            'target': 'new',
            'context': {'body': html}
        }
