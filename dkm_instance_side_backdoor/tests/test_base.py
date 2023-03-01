from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBase, cls).setUpClass()
        cls.env = cls.env(context={**cls.env.context, **{
            'tracking_disable': True,
            'no_reset_password': True,
            'test_mode': True
        }})
        cls.token1, cls.token2 = cls.env['dkm.token'].create([
            {'name': 'token1', 'token': '1x3'},
            {'name': 'token2', 'token': '1x4'},
        ])

    @classmethod
    def patch_datetime_now(cls, now):
        return patch('odoo.fields.Datetime.now', return_value=now)

    @classmethod
    def patch_date_today(cls, today):
        return patch('odoo.fields.Date.today', return_value=today)

    @classmethod
    def patch_datetime_cursor_now(cls, now):
        return patch('odoo.sql_db.Cursor.now', return_value=now)
