from json import loads
from kikiutils.check import isdict
from typing import Union
from validator import validate as _package_validate

from ..classes.transmission import DataTransmissionSecret


async def data_transmission_exec(
    hash_data: Union[bytes, str],
    secret_classes: tuple[DataTransmissionSecret],
    error_404,
    parse_json: bool,
    kwarg_name: str,
    view_func,
    args: tuple,
    kwargs: dict,
    is_blacksheep: bool = False
):
    for secret_class in secret_classes:
        data: dict = secret_class.data_transmission.process_hash_data(
            hash_data
        )

        if data is not None:
            break
    else:
        return error_404

    if parse_json:
        parse_dict_value_json(data)

    if is_blacksheep:
        result = await view_func(*args[:-1], data, **kwargs)
    else:
        kwargs[kwarg_name] = data
        result = await view_func(*args, **kwargs)

    response_data = {
        'success': True
    }

    if isdict(result):
        response_data.update(result)
    elif result is None:
        response_data['success'] = False
    elif result != True:
        return result

    return secret_class.data_transmission.hash_data(response_data)


def parse_dict_value_json(data: dict):
    for k, v in data.items():
        try:
            data[k] = loads(v)
        except:
            pass


async def validate_and_exec(
    rules: dict[str],
    request_data: dict[str, str],
    parse_json: bool,
    use_dict: bool,
    view_func,
    args: tuple,
    kwargs: dict
):
    # Strip data
    for k, v in request_data.items():
        request_data[k] = v.strip()

    # Validate
    result, data, _ = _package_validate(
        request_data,
        rules,
        True
    )

    if result:
        if parse_json:
            parse_dict_value_json(data)

        if use_dict:
            kwargs['data'] = data
        else:
            kwargs.update(data)

        return await view_func(*args, **kwargs)
