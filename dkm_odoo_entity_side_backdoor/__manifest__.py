{
    'name': 'Odoo entity health monitoring',
    'description': "Odoo entity health monitoring",
    'version': '1.0.0',
    'category': "Tools",
    'depends': ['dkm_api'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OPL-1',
}
