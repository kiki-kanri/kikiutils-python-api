from blacksheep import not_found, WebSocket
from functools import wraps
from kikiutils.aes import AesCrypt


def service_websocket(aes: AesCrypt):
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(*args):
            for arg in args:
                if isinstance(arg, WebSocket):
                    if extra_info := arg.headers.get(b'extra-info'):
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
