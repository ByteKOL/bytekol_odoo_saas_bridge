from unittest.mock import patch

from odoo.tests.common import tagged
from dateutil.relativedelta import relativedelta
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDkmToken(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestDkmToken, cls).setUpClass()
        cls.env = cls.env(context={**cls.env.context, **{
            'test_mode': True
        }})
        cls.token1, cls.token2 = cls.env['dkm.token'].create([
            {'name': 'token1', 'token': '1x3'},
            {'name': 'token2', 'token': '1x4'},
        ])

    def test_is_expire_and_date_expire_and_is_permanent(self):
        # live time = 0 => is not expire
        self.assertEqual(self.token1.live_time, 0)
        self.assertFalse(self.token1._is_expire())
        self.assertTrue(self.token1.is_permanent)

        self.token1.live_time = 10
        self.assertRecordValues(self.token1, [{
            'date_expire': self.token1.create_date + relativedelta(seconds=10),
        }])
        self.assertFalse(self.token1._is_expire())
        now = self.token1.create_date + relativedelta(seconds=11)
        with patch('odoo.fields.Datetime.now', return_value=now):
            self.assertTrue(self.token1._is_expire())

    def test_is_token_valid(self):
        token_txt = '888x29xk1s'
        new_token = self.env['dkm.token'].create({
            'token': token_txt,
            'name': 'n1',
            'purpose': 'api_general',
            'live_time': 10
        })

        self.assertTrue(self.env['dkm.token'].is_token_valid(token_txt, 'api_general'))
        self.assertFalse(self.env['dkm.token'].is_token_valid(token_txt, 'gg33'))
        now = new_token.create_date + relativedelta(seconds=11)
        with patch('odoo.fields.Datetime.now', return_value=now):
            self.assertFalse(self.env['dkm.token'].is_token_valid(token_txt, 'api_general'))
