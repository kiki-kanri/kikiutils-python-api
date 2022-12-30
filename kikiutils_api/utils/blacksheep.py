from blacksheep import Request, WebSocket
from typing import Callable, Optional, TypeVar, Union


T = TypeVar('T')
_is_ip_header_names = {
    b'client-ip',
    b'x-forwarded-for',
    b'x-real-ip',
    b'remote_addr'
}

_is_rq = lambda x: isinstance(x, Request)
_is_ws = lambda x: isinstance(x, WebSocket)


def _get_list_item(args: list[T], func: Callable[[T], bool]):
    for arg in args:
        if func(arg):
            return arg


async def get_file(rq: Request, file_name: str):
    bfile_name = file_name.encode()
    files = await rq.files()
    return _get_list_item(files, lambda x: x.name == bfile_name)


def get_ip(rq_or_ws: Union[Request, WebSocket]):
    for name in _is_ip_header_names:
        if ip := rq_or_ws.headers.get(name):
            return ip[0].decode()


def get_rq(args: tuple) -> Optional[Request]:
    return _get_list_item(args, lambda x: _is_rq(x))


def get_ws(args: tuple) -> Optional[WebSocket]:
    return _get_list_item(args, lambda x: _is_ws(x))
