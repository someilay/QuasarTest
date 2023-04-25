import unittest
import os

from sqlalchemy import create_engine, Engine

from datetime import datetime, timedelta
from src.app import app
from src.models import data_models


def get_now() -> datetime:
    """
    Get datetime without milliseconds

    :return: now
    :rtype: datetime
    """
    now = datetime.now()
    return datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)


class TestMetrics(unittest.TestCase):
    engine: Engine

    @classmethod
    def setUpClass(cls) -> None:
        unittest.TestLoader.sortTestMethodsUsing = None

        engine = create_engine('sqlite:///test.db')
        data_models.setup(engine)

        now = get_now()
        cls.engine = engine
        cls.app = app.test_client()
        users = [{'username': 'a', 'email': 'a', 'registration_date': now}]

        for i in range(1, 5):
            cur = dict(users[-1])
            cur['username'] += 'a'
            cur['registration_date'] = now - timedelta(days=i * 3)
            cur['email'] = 'a' if i % 2 == 0 else 'b'
            users.append(cur)

        for user in users:
            data_models.User(**user).add()

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove('test.db')
        cls.engine.dispose()

    def test_last_registered(self):
        res: dict = self.app.get('/user/last_registered', json=dict()).json
        self.assertEqual(res.get('result'), 3)

        res: dict = self.app.get('/user/last_registered', json={'last_n_days': 3}).json
        self.assertEqual(res.get('result'), 1)

    def test_longest_names(self):
        res: dict = self.app.get('/user/longest_names', json=dict()).json
        self.assertEqual(len(res.get('result')), 5)
        self.assertEqual(res.get('result')[-1].get('username'), 'a')

        res: dict = self.app.get('/user/longest_names', json={'top_n': 3}).json
        self.assertEqual(len(res.get('result')), 3)
        self.assertEqual(res.get('result')[-1].get('username'), 'aaa')

    def test_email_domain(self):
        res: dict = self.app.get('/user/email_domain', json={'domain': 'a'}).json
        self.assertEqual(res.get('result'), 3 / 5)

        res: dict = self.app.get('/user/email_domain', json={'domain': 'b'}).json
        self.assertEqual(res.get('result'), 2 / 5)


if __name__ == '__main__':
    unittest.main()
