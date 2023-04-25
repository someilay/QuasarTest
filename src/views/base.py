from flask import Blueprint, jsonify, request, Response
from datetime import datetime

from src.models import data_models
from src.middleware.body_type import correct_body, check_fields
from src.utils.predict import activity_prob


base = Blueprint(name='base', import_name=__name__)


@base.route('/echo', methods=['POST'])
@correct_body
def test() -> Response:
    return jsonify(request.json)


@base.route('/user/add', methods=['PUT'])
@correct_body
@check_fields(username=str, email=str, id=int | None)
def add_user() -> Response:
    content: dict = request.json
    username: str = content.get('username', None)
    email: str = content.get('email', None)
    _id: int | None = content.get('id', None)

    user = data_models.User(id=_id, username=username, email=email, registration_date=datetime.now()).add()

    if not user:
        return jsonify(error=2, error_msg='user with given id is already present in the table!')

    return jsonify(user.to_dict())


@base.route('/user/get', methods=['GET'])
@correct_body
@check_fields(username=str | None, email=str | None, id=int | None)
def get_user() -> Response:
    content: dict = request.json
    username: str | None = content.get('username', None)
    email: str | None = content.get('email', None)
    _id: int | None = content.get('id', None)

    if not (_id or email or username):
        return jsonify(error=1, error_msg='at least one field should be specified!')

    if _id is not None:
        user = data_models.User.get(data_models.User.id == _id)
    elif username:
        user = data_models.User.get(data_models.User.username == username)
    else:
        user = data_models.User.get(data_models.User.email == email)

    if not user:
        return jsonify(error=3, error_msg='No such user!')

    activity = activity_prob(data_models.Activity.get_activity_by_months(user.id))
    ret_dict = user.to_dict()
    ret_dict['activity_prob'] = activity

    return jsonify(ret_dict)


@base.route('/user/update', methods=['POST'])
@correct_body
@check_fields(username=str | None, email=str | None, id=int)
def update_user() -> Response:
    content: dict = request.json
    username: str | None = content.get('username', None)
    email: str | None = content.get('email', None)
    _id: int = content.get('id')

    user = data_models.User.get(data_models.User.id == _id)
    if not user:
        return jsonify(error=3, error_msg='User has been deleted!')

    if username:
        user.username = username
    if email:
        user.email = email
    if not user.update():
        return jsonify(user.to_dict())

    return jsonify(user.to_dict())


@base.route('/user/delete', methods=['DELETE'])
@correct_body
@check_fields(username=str | None, email=str | None, id=int | None)
def delete_user() -> Response:
    content: dict = request.json
    username: str | None = content.get('username', None)
    email: str | None = content.get('email', None)
    _id: int | None = content.get('id')

    if not (_id or email or username):
        return jsonify(error=1, error_msg='at least one field should be specified!')

    if _id is not None:
        res = data_models.User.delete(data_models.User.id == _id)
    elif username:
        res = data_models.User.delete(data_models.User.username == username)
    else:
        res = data_models.User.delete(data_models.User.email == email)

    if not res:
        return jsonify(error=3, error_msg='User has been deleted!')

    return jsonify(status='ok')


@base.route('/user/all', methods=['GET'])
@correct_body
@check_fields(page=int | None, per_page=int | None)
def all_users() -> Response:
    content: dict = request.json
    page = content.get('page', 0)
    per_page = content.get('per_page', 10)

    users = [user.to_dict() for user in data_models.User.pagination(page, per_page)]

    return jsonify(users=users)
