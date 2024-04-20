{
    'name': 'Bytekol Odoo SaaS Bridge',
    'description': "Bytekol Odoo SaaS Bridge",
    'version': '1.0.0',
    'category': "Tools",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/bk_token_views.xml',
        'views/bk_traceback_log_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/bytekol_odoo_saas_bridge/static/src/js/odoo_saas_error_dialog.js',
        ],
    },
    'installable': True,
    'auto_install': True,
    'license': 'OPL-1',
}
