from functools import wraps
from kikiutils.check import isstr
from sanic import Request, text

from ..classes.transmission import DataTransmissionSecret
from ..utils import data_transmission_exec, validate_and_exec
from ..utils.sanic import get_request_data


_error_404 = text('', 404)
_error_422 = text('', 422)


# DataTransmission

def data_transmission_api(
    *secret_classes: DataTransmissionSecret,
    parse_json: bool = True,
    kwarg_name: str = 'data'
):
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(rq: Request, *args, **kwargs):
            if (hash_file := rq.files.get('hash_file')) is None:
                return _error_404

            result = await data_transmission_exec(
                hash_file.body,
                secret_classes,
                _error_404,
                parse_json,
                kwarg_name,
                view_func,
                (rq, *args),
                kwargs
            )

            if isstr(result):
                return text(result)
            return result
        return wrapped_view
    return decorator


# Validate

def validate(
    rules: dict,
    parse_json: bool = False,
    use_dict: bool = False
):
    """Validate request data."""

    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(rq: Request, *args, **kwargs):
            request_data = get_request_data(rq)
            result = await validate_and_exec(
                rules,
                request_data,
                parse_json,
                use_dict,
                view_func,
                (rq, *args),
                kwargs
            )

            if result is None:
                return _error_422
            return result
        return wrapped_view
    return decorator
