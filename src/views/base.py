from flask import Blueprint, jsonify, request, Response
from datetime import datetime

from src.models import data_models
from src.middleware.body_type import correct_body, check_fields
from src.utils.predict import activity_prob


base = Blueprint(name='base', import_name=__name__)


def to_datetime(date_str: str | None) -> datetime | None:
    """
    Converts string to datetime

    :param date_str: input string
    :type date_str: str | None
    :return: converted datetime
    :rtype: datetime | None
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%d-%m-%Y %H:%M:%S')
    except ValueError:
        return None


def handle_datetime(date_str: str | None) -> tuple[datetime | None, Response | None]:
    """
    Handle datetime string

    :param date_str: input string
    :type date_str: str | None
    :return: error response if occurs and converted datetime
    :rtype: tuple[Response | None, datetime | None]
    """
    date: datetime | None = None
    if date_str:
        date = to_datetime(date_str)
    if not date and date_str:
        return date, jsonify(error=1, error_msg='registration_date should be in the format DD-MM-YYYY hh:mm:ss')
    return date, None


def get_now() -> datetime:
    """
    Get datetime without milliseconds

    :return: now
    :rtype: datetime
    """
    now = datetime.now()
    return datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)


@base.route('/echo', methods=['POST'])
@correct_body
def test() -> Response:
    """
    Echo view. Returns payload as answer

    :return: response
    :rtype: Response
    """
    return jsonify(request.json)


@base.route('/user/add', methods=['PUT'])
@correct_body
@check_fields(username=str, email=str, registration_date=str | None, id=int | None)
def add_user() -> Response:
    """
    Adds user to table. Registration date is set as now.

    :return: response
    :rtype: Response
    """
    content: dict = request.json
    username: str = content.get('username', None)
    email: str = content.get('email', None)
    registration_date: str | None = content.get('registration_date', None)
    _id: int | None = content.get('id', None)

    # Check datetime format
    date, error = handle_datetime(registration_date)
    if error:
        return error
    if not date:
        date = get_now()

    user = data_models.User(id=_id, username=username, email=email, registration_date=date).add()

    if not user:
        return jsonify(error=2, error_msg='user with given id is already present in the table!')

    return jsonify(user.to_dict())


@base.route('/user/get', methods=['GET'])
@correct_body
@check_fields(username=str | None, email=str | None, registration_date=str | None, id=int | None, predict=bool | None)
def get_user() -> Response:
    """
    Get user from the table by filters from requests

    :return: response
    :rtype: Response
    """
    content: dict = request.json
    username: str | None = content.get('username', None)
    email: str | None = content.get('email', None)
    _id: int | None = content.get('id', None)
    registration_date: str | None = content.get('registration_date', None)
    predict: bool | None = content.get('predict', None)

    if not (_id or email or username or registration_date):
        return jsonify(error=1, error_msg='at least one field should be specified!')

    # Check datetime format
    date, error = handle_datetime(registration_date)
    if error:
        return error

    if _id is not None:
        user = data_models.User.get(data_models.User.id == _id)
    elif username:
        user = data_models.User.get(data_models.User.username == username)
    elif email:
        user = data_models.User.get(data_models.User.email == email)
    else:
        user = data_models.User.get(data_models.User.registration_date == date)

    if not user:
        return jsonify(error=3, error_msg='No such user!')

    ret_dict = user.to_dict()
    if predict is not None and predict:
        activity = activity_prob(data_models.Activity.get_activity_by_months(user.id))
        ret_dict['activity_prob'] = activity

    return jsonify(ret_dict)


@base.route('/user/update', methods=['POST'])
@correct_body
@check_fields(username=str | None, email=str | None, registration_date=str | None, id=int)
def update_user() -> Response:
    """
    Update user in the table by id within a given new fields

    :return: response
    :rtype: Response
    """
    content: dict = request.json
    username: str | None = content.get('username', None)
    email: str | None = content.get('email', None)
    registration_date: str | None = content.get('registration_date', None)
    _id: int = content.get('id')

    # Check date format
    date, error = handle_datetime(registration_date)
    if error:
        return error

    user = data_models.User.get(data_models.User.id == _id)
    if not user:
        return jsonify(error=3, error_msg='User has been deleted!')

    if username:
        user.username = username
    if email:
        user.email = email
    if date:
        user.registration_date = date
    if not user.update():
        return jsonify(user.to_dict())

    return jsonify(user.to_dict())


@base.route('/user/delete', methods=['DELETE'])
@correct_body
@check_fields(username=str | None, email=str | None, registration_date=str | None, id=int | None)
def delete_user() -> Response:
    """
    Delete user from the table by a given filter

    :return: response
    :rtype: Response
    """
    content: dict = request.json
    username: str | None = content.get('username', None)
    email: str | None = content.get('email', None)
    registration_date: str | None = content.get('registration_date', None)
    _id: int | None = content.get('id')

    if not (_id or email or username or registration_date):
        return jsonify(error=1, error_msg='at least one field should be specified!')

    # Check date format
    date, error = handle_datetime(registration_date)
    if error:
        return error

    if _id is not None:
        res = data_models.User.delete(data_models.User.id == _id)
    elif username:
        res = data_models.User.delete(data_models.User.username == username)
    elif email:
        res = data_models.User.delete(data_models.User.email == email)
    else:
        res = data_models.User.delete(data_models.User.registration_date == date)

    if not res:
        return jsonify(error=3, error_msg='User has been deleted!')

    return jsonify(status='ok')


@base.route('/user/all', methods=['GET'])
@correct_body
@check_fields(page=int | None, per_page=int | None)
def all_users() -> Response:
    """
    Perform pagination, parameters passed in request payload

    :return: response
    :rtype: Response
    """
    content: dict = request.json
    page = content.get('page', 0)
    per_page = content.get('per_page', 10)

    users = [user.to_dict() for user in data_models.User.pagination(page, per_page)]

    return jsonify(users=users)
