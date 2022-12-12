from blacksheep import Request, WebSocket
from typing import Callable, TypeVar


T = TypeVar('T')
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


def get_rq(args: tuple) -> Request | None:
    return _get_list_item(args, lambda x: _is_rq(x))


def get_ws(args: tuple) -> WebSocket | None:
    return _get_list_item(args, lambda x: _is_ws(x))
