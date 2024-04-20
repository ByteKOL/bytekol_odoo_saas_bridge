from . import models
from . import controllers


import odoo
import logging
_logger = logging.getLogger(__name__)

if 'dkm_odoo_entity_side_backdoor' not in odoo.tools.config.get('server_wide_modules', '').split(','):
    _logger.error('module dkm_odoo_entity_side_backdoor must be loaded in server_wide_modules')
