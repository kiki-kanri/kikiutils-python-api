from sanic import Request


def get_request_data(rq: Request):
    try:
        request_data: dict = rq.json
    except:
        request_data = {}

        for k in rq.form:
            request_data[k] = rq.form.get(k)

    return request_data
