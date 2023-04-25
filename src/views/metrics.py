from flask import Blueprint, jsonify, request, Response

from src.models import data_models
from src.middleware.body_type import correct_body, check_fields


metrics = Blueprint(name='metrics', import_name=__name__)


@metrics.route('/user/last_registered', methods=['GET'])
@correct_body
@check_fields(last_n_days=int | None)
def last_registered() -> Response:
    """
    Return number of users registered a given last_n_days

    :return: response
    :rtype: Response
    """
    content: dict = request.json
    last_n_days: int | None = content.get('last_n_days', None)

    res = data_models.User.registered_last(last_n_days or 7)
    return jsonify(result=res)


@metrics.route('/user/longest_names', methods=['GET'])
@correct_body
@check_fields(top_n=int | None)
def longest_names() -> Response:
    """
    List of users with the longest names, return top_n users

    :return: response
    :rtype: Response
    """
    content: dict = request.json
    top_n: int | None = content.get('top_n', None)

    longest = [user.to_dict() for user in data_models.User.longest_names(top_n or 5)]
    return jsonify(result=longest)


@metrics.route('/user/email_domain', methods=['GET'])
@correct_body
@check_fields(domain=str)
def email_domain() -> Response:
    """
    Fraction of users with email in a given domain

    :return: response
    :rtype: Response
    """
    content: dict = request.json
    domain: str = content.get('domain')

    fraction = data_models.User.percent_emails_endswith(domain)
    return jsonify(result=fraction)
