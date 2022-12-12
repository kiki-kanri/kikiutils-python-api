from blacksheep import not_found
from functools import wraps
from kikiutils.aes import AesCrypt

from ..classes.transmission import DataTransmissionSecret
from ..utils import data_transmission_exec
from ..utils.blacksheep import get_file, get_rq, get_ws


def data_transmission_api(
    *secret_classes: DataTransmissionSecret,
    parse_json: bool = True,
    kwarg_name: str = 'data'
):
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(*args, **kwargs):
            if (rq := get_rq(args)) is None:
                return not_found()

            if (hash_file := await get_file(rq, 'hash_file')) is None:
                return not_found()

            result = await data_transmission_exec(
                hash_file.data,
                secret_classes,
                not_found(),
                parse_json,
                kwarg_name,
                view_func,
                args,
                kwargs,
                True
            )

            return result
        return wrapped_view
    return decorator


def service_websocket(aes: AesCrypt):
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(*args):
            if ws := get_ws(args):
                if extra_info := ws.headers.get(b'extra-info'):
                    try:
                        return await view_func(
                            *args[:-1],
                            aes.decrypt(extra_info[0])
                        )
                    except:
                        pass

            return not_found()
        return wrapped_view
    return decorator
