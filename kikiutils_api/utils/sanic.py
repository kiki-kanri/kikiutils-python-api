from kikiutils.json import dict_key_camel_to_snake
from sanic import Request, text


error = text('error', 500)
rp_403 = text('', 403)
rp_404 = text('', 404)
rp_409 = text('', 409)
rp_422 = text('', 422)
success = text('success')


def get_request_data(rq: Request) -> dict[str]:
    try:
        if (request_data := rq.json) is None:
            raise ValueError()
    except:
        request_data = {}
        rq_kwargs = rq.form or rq.args

        for k in rq_kwargs:
            request_data[k] = rq_kwargs.get(k)

    return dict_key_camel_to_snake(request_data)
