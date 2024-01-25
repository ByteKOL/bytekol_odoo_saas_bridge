{
    'name': 'Odoo entity health monitoring',
    'description': "Odoo entity health monitoring",
    'version': '1.0.0',
    'category': "Tools",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/dkm_token_views.xml',
        'views/dkm_traceback_log_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/dkm_odoo_entity_side_backdoor/static/src/js/odoo_saas_error_dialog.js',
        ],
    },
    'installable': True,
    'auto_install': True,
    'license': 'OPL-1',
}
