from flask import jsonify, request, Response
from typing import Callable
from functools import wraps

from types import UnionType


def correct_body(view: Callable[[], Response]) -> Callable[[], Response]:
    """
    Decorator that checks that request contains json as payloda

    :param view: function to decorate
    :rtype view: Callable[[], Response]
    :return: wrapper
    :rtype: Callable[[], Response]
    """
    @wraps(view)
    def _correct_body() -> Response:
        if not request.is_json:
            return jsonify(error=0, error_msg='Incorrect body type, should be a json!')
        return view()

    return _correct_body


def check_fields(**kwargs: type | UnionType) -> Callable[[], Callable[[], Response]]:
    """
    Decorator that checks that a given json contains a needed fields with needed type

    :param kwargs: filed name with a possible type
    :type kwargs: type | UnionType
    :return: decorator
    :rtype: Callable[[], Callable[[], Response]]
    """
    def _check_fields(view: Callable[[], Response]) -> Callable[[], Response]:
        @wraps(view)
        def __check_fields() -> Response:
            content: dict = request.json
            for key, t in kwargs.items():
                val = content.get(key, None)
                t_str = t.__name__ if isinstance(t, type) else str(t)
                if val is None and not isinstance(val, t):
                    return jsonify(error=1, error_msg=f'{key} should be specified!')
                if not isinstance(val, t):
                    return jsonify(error=1, error_msg=f'Incorrect type for {key}, should be {t_str}')
            return view()

        return __check_fields

    return _check_fields
