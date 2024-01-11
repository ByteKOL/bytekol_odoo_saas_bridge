{
    'name': 'Odoo entity health monitoring',
    'description': "Odoo entity health monitoring",
    'version': '1.0.0',
    'category': "Tools",
    'depends': ['dkm_api'],
    'data': [
        'security/ir.model.access.csv',
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
