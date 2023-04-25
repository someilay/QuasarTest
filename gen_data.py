import names

from random import choice, random, randint
from datetime import datetime, timedelta

from src import config
from src.models.data_models import Activity, User


EMAILS = ['gmail.com', 'yandex.ru', 'yahoo.com', 'mail.ru', 'bing.com']


def get_random_user() -> User:
    """
    Generate a random user

    :return: generated user
    :rtype: User
    """
    username, last = names.get_full_name().split()
    email = username.lower() + last + str(randint(1960, 2010)) + '@'
    registration = datetime.now() - timedelta(days=randint(90, 365 * 2), seconds=randint(0, 3600 * 24))

    if random() < 0.8:
        email += choice(EMAILS)
    else:
        email += username.lower() + choice(['.ru', '.com'])

    return User(username=username, email=email, registration_date=registration)


def get_random_activity(user: User) -> Activity:
    """
    Generate random activity for given user.
    Generated date is in the range [registration date, now]

    :param user: the target
    :type user: User
    :return: generated activity
    :rtype: Activity
    """
    registration: datetime = user.registration_date
    seconds = int((datetime.now() - registration).total_seconds())
    return Activity(
        user_id=user.id,
        date=registration + timedelta(seconds=randint(0, seconds))
    )


def gen_data(n: int = 50, a: int = 100):
    """
    Generate a fake data and insert it into local db

    :param n: amount of users to generate
    :type n: int
    :param a: maximum number of activities per user
    :type a: int
    """
    for i in range(n):
        user = get_random_user().add()
        for _ in range(randint(1, a)):
            get_random_activity(user).add()
        print(f'User: {user}; Added, activities generated!')


if __name__ == '__main__':
    gen_data()
