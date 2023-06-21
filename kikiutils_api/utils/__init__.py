from inspect import signature
from kikiutils.check import isdict
from kikiutils.json import oloads
from typing import Callable, Union

from ..classes.transmission import DataTransmission


async def data_transmission_exec(
    hash_data: Union[bytes, str],
    secret_classes: tuple[DataTransmission],
    error_404,
    parse_json: bool,
    kwarg_name: str,
    view_func,
    args: tuple,
    kwargs: dict,
    is_blacksheep: bool = False
):
    for secret_class in secret_classes:
        data: dict = secret_class.process_hash_data(hash_data)

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

    return secret_class.hash_data(response_data)


def get_func_annotation_index(func: Callable, annotation_type):
    parameter_values = signature(func).parameters.values()

    for i, v in enumerate(parameter_values):
        if v.annotation is annotation_type:
            return i

    raise ValueError(
        f'Function {func} need set type {annotation_type} parameter!'
    )


def parse_dict_value_json(data: dict):
    for k, v in data.items():
        try:
            data[k] = oloads(v)
        except:
            pass
