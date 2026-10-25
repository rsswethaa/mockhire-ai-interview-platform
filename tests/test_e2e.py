import unittest

import app as app_module


class EndToEndSmokeTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()

    def test_health_home_and_platform_status(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        self.assertEqual(self.client.get('/').status_code, 200)
        status = self.client.get('/api/platform/status')
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.get_json()['auth'])

    def test_auth_register_login_round_trip(self):
        email = 'ci-mockhire@example.com'
        register = self.client.post('/api/auth/register', json={'email': email, 'password': 'portfolio123'})
        self.assertIn(register.status_code, (200, 409))
        login = self.client.post('/api/auth/login', json={'email': email, 'password': 'portfolio123'})
        self.assertEqual(login.status_code, 200)
        token = login.get_json()['token']
        me = self.client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(me.status_code, 200)


if __name__ == '__main__':
    unittest.main()
