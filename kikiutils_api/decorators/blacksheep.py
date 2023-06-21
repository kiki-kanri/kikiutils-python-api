from blacksheep import not_found, Request, WebSocket
from functools import wraps
from kikiutils.aes import AesCrypt

from ..classes.transmission import DataTransmission
from ..utils import data_transmission_exec, get_func_annotation_index
from ..utils.blacksheep import get_file


def data_transmission_api(*secret_classes: DataTransmission, parse_json: bool = True, kwarg_name: str = 'data'):
    def decorator(view_func):
        rq_index = get_func_annotation_index(view_func, Request)

        @wraps(view_func)
        async def wrapped_view(*args):
            if (hash_file := await get_file(args[rq_index], 'hash_file')) is None:
                return not_found()

            result = await data_transmission_exec(
                hash_file.data,
                secret_classes,
                not_found(),
                parse_json,
                kwarg_name,
                view_func,
                args,
                {},
                True
            )

            return result
        return wrapped_view
    return decorator


def service_websocket(aes: AesCrypt):
    def decorator(view_func):
        ws_index = get_func_annotation_index(view_func, WebSocket)

        @wraps(view_func)
        async def wrapped_view(*args):
            if extra_info := args[ws_index].headers.get(b'extra-info'):
                try:
                    data = aes.decrypt(extra_info[0])
                except:
                    return

                return await view_func(*args[:-1], data)

        return wrapped_view
    return decorator
