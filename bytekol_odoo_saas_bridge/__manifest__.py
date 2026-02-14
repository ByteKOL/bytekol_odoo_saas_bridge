{
    'name': 'SaaS Bridge',
    'description': "SaaS Bridge",
    'version': '1.0.1',
    'category': "Tools",
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/bk_token_views.xml',
        'views/bk_traceback_log_views.xml',
        'views/simple_queue_job_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/bytekol_odoo_saas_bridge/static/src/js/odoo_saas_error_dialog.js',
            '/bytekol_odoo_saas_bridge/static/src/toolbar/*',
            '/bytekol_odoo_saas_bridge/static/src/dialogs/*',
        ],
    },
    'installable': True,
    'auto_install': True,
    'license': 'OPL-1',
}
