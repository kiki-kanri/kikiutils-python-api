from sanic import Request


def get_request_data(rq: Request) -> dict[str]:
    try:
        if (request_data := rq.json) is None:
            raise ValueError()
    except:
        request_data = {}
        rq_kwargs = rq.form or rq.args

        for k in rq_kwargs:
            request_data[k] = rq_kwargs.get(k)

    return request_data
