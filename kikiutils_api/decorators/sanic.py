from functools import wraps
from kikiutils.aes import AesCrypt
from kikiutils.check import isstr
from kikiutils.json import oloads
from sanic import Request, text
from sanic.server.websockets.connection import WebSocketConnection

from ..classes.transmission import DataTransmissionSecret
from ..utils import data_transmission_exec
from ..utils.sanic import get_request_data, rp_404, rp_422


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
                return rp_404

            result = await data_transmission_exec(
                hash_file.body,
                secret_classes,
                rp_404,
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

class BaseClass:
    pass


def validate(rules: BaseClass, data_name: str = 'data'):
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(rq: Request, *args, **kwargs):
            request_data = get_request_data(rq)
            inited_rules = rules()
            rules_dicts = rules.__dict__

            for key, value_tpye in rules.__annotations__.items():
                if (rq_value := request_data.get(key)) is None:
                    if key not in rules_dicts:
                        return rp_422
                    else:
                        setattr(inited_rules, key, rules_dicts[key])
                else:
                    try:
                        if value_tpye is bool:
                            try:
                                rq_value = rq_value.lower() == 'true'
                            except:
                                pass

                        if value_tpye is dict or value_tpye is list:
                            setattr(
                                inited_rules,
                                key,
                                rq_value if isinstance(rq_value, (dict, list)) else oloads(rq_value)
                            )
                        else:
                            setattr(inited_rules, key, value_tpye(rq_value))
                    except:
                        return rp_422

            kwargs[data_name] = inited_rules
            return await view_func(rq, *args, **kwargs)
        return wrapped_view
    return decorator


# Websocket

def service_websocket(aes: AesCrypt):
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(
            rq: Request,
            ws: WebSocketConnection,
            *args,
            **kwargs
        ):
            if extra_info := rq.headers.get('extra-info'):
                try:
                    data = aes.decrypt(extra_info)
                except:
                    return

                return await view_func(rq, ws, extra_data=data, *args, **kwargs)

        return wrapped_view
    return decorator
