from blacksheep import FromFiles, FormPart, Request, text
from functools import wraps
from kikiutils.check import isstr
from kikiutils.string import b2s

from ..classes import DataTransmissionSecret
from ..utils import data_transmission_exec


def data_transmission_api(
    *secret_classes: DataTransmissionSecret,
    parse_json: bool = True,
    kwarg_name: str = 'data'
):
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(rq: Request, files: FromFiles, *args, **kwargs):
            dict_files = get_request_files_dict(files)

            if (hash_file := dict_files.get('hash_file')) is None:
                return text('', 404)

            result = await data_transmission_exec(
                hash_file.data,
                secret_classes,
                text('', 404),
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


def get_request_files_dict(files: FromFiles) -> dict[str, FormPart]:
    return {
        b2s(file.data): file
        for file in files.value
    }


def process_request_files(kwarg_name: str = 'files'):
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(
            rq: Request,
            files: FromFiles,
            *args,
            **kwargs
        ):
            kwargs[kwarg_name] = get_request_files_dict(files)
            return await view_func(rq, *args, **kwargs)
        return wrapped_view
    return decorator
