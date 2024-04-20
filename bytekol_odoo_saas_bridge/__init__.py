from . import models
from . import controllers


import odoo
import logging
_logger = logging.getLogger(__name__)

if 'bytekol_odoo_saas_bridge' not in odoo.tools.config.get('server_wide_modules', '').split(','):
    _logger.error('module bytekol_odoo_saas_bridge must be loaded in server_wide_modules')
