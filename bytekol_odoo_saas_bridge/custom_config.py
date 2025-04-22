from odoo.tools import config as odoo_config

import configparser
custom_config = configparser.ConfigParser()
custom_config.read(odoo_config.rcfile)
