import unittest
import os

from sqlalchemy import create_engine, Engine

from src.app import app
from src.models import data_models


class TestBase(unittest.TestCase):
    engine: Engine

    @classmethod
    def setUpClass(cls) -> None:
        unittest.TestLoader.sortTestMethodsUsing = None

        engine = create_engine('sqlite:///test.db')
        data_models.setup(engine)

        cls.app = app.test_client()
        cls.engine = engine
        cls.user_inv_1 = {'username': 'user'}
        cls.user_inv_2 = {'username': 1, 'email': 1}
        cls.user_inv_3 = {'username': 'c', 'email': 'd', 'id': 1}
        cls.user_inv_4 = {'username': 'c', 'email': 'd', 'registration_date': '00-00-0000 00:00:00'}
        cls.user_1 = {'username': 'a', 'email': 'b'}
        cls.user_2 = {'username': 'c', 'email': 'd', 'id': 2}
        cls.user_3 = {'username': 'c', 'email': 'd', 'registration_date': '01-01-2000 00:00:00'}

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove('test.db')
        cls.engine.dispose()

    def test_payload_check(self):
        ret = self.app.post('/echo')
        self.assertTrue(ret.is_json)
        self.assertEqual(ret.json.get('error_msg', None), 'Incorrect body type, should be a json!')

    def test_echo(self):
        data = {'msg': 'Hello!'}
        ret = self.app.post('/echo', json=data)
        self.assertEqual(ret.json, data)

    def test_add_corrupted_payload(self):
        data = {}
        ret: dict = self.app.put('/user/add', json=data).json
        self.assertTrue(ret.get('error_msg', '').endswith('should be specified!'))

        ret: dict = self.app.put('/user/add', json=self.user_inv_1).json
        self.assertTrue(ret.get('error_msg', '').endswith('should be specified!'))

        ret: dict = self.app.put('/user/add', json=self.user_inv_2).json
        self.assertTrue(ret.get('error_msg', '').startswith('Incorrect type for'))

        ret: dict = self.app.put('/user/add', json=self.user_inv_4).json
        self.assertTrue(
            ret.get('error_msg', '').startswith('registration_date should be in the format DD-MM-YYYY hh:mm:ss')
        )

    def test_add(self):
        ret: dict = self.app.put('/user/add', json=self.user_1).json
        self.assertEqual(ret.get('username', None), self.user_1.get('username'))
        self.assertEqual(ret.get('email', None), self.user_1.get('email'))

        ret: dict = self.app.put('/user/add', json=self.user_inv_3).json
        self.assertEqual(ret.get('error_msg', None), 'user with given id is already present in the table!')

        ret: dict = self.app.put('/user/add', json=self.user_2).json
        self.assertEqual(ret.get('username', None), self.user_2.get('username'))
        self.assertEqual(ret.get('email', None), self.user_2.get('email'))
        self.assertEqual(ret.get('id', None), self.user_2.get('id'))

        ret: dict = self.app.put('/user/add', json=self.user_3).json
        self.assertEqual(ret.get('username', None), self.user_3.get('username'))
        self.assertEqual(ret.get('email', None), self.user_3.get('email'))

    def test_get(self):
        ret: dict = self.app.get('/user/get', json=dict()).json
        self.assertEqual(ret.get('error_msg', None), 'at least one field should be specified!')

        ret: dict = self.app.get('/user/get', json={'username': 'e'}).json
        self.assertEqual(ret.get('error_msg', None), 'No such user!')

        ret: dict = self.app.get('/user/get', json={'username': self.user_1.get('username')}).json
        self.assertEqual(ret.get('username', None), self.user_1.get('username'))
        self.assertEqual(ret.get('email', None), self.user_1.get('email'))

    def test_get_prob(self):
        users = data_models.User.pagination()
        for user in users:
            data_models.Activity(user_id=user.id, date=user.registration_date).add()

            ret: dict = self.app.get('/user/get', json={'id': user.id, 'predict': True}).json
            self.assertTrue(ret.get('activity_prob', None) is not None)
            self.assertTrue(ret.get('activity_prob') > 0)

    def test_update(self):
        self.user_1['id'] = 1
        self.user_1['username'] *= 2
        self.app.post('/user/update', json=self.user_1)
        self.assertEqual(
            data_models.User.get(data_models.User.id == self.user_1['id']).username,
            self.user_1['username']
        )

        self.user_2['id'] = 2
        self.user_2['username'] *= 2
        self.app.post('/user/update', json=self.user_2)
        self.assertEqual(
            data_models.User.get(data_models.User.id == self.user_2['id']).username,
            self.user_2['username']
        )

    def test_delete(self):
        ret = self.app.delete('/user/delete', json={'registration_date': self.user_3['registration_date']}).json
        self.assertEqual(ret.get('status'), 'ok')
        self.assertTrue(
            not data_models.User.get(data_models.User.registration_date == self.user_3['registration_date'])
        )

    def test_pagination(self):
        ret: dict = self.app.get('/user/all', json=dict()).json
        self.assertEqual(len(ret.get('users')), 2)

        ret: dict = self.app.get('/user/all', json={'per_page': 1}).json
        self.assertEqual(len(ret.get('users')), 1)

        ret: dict = self.app.get('/user/all', json={'page': 1, 'per_page': 1}).json
        self.assertEqual(len(ret.get('users')), 1)


if __name__ == '__main__':
    unittest.main()
