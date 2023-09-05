from abc import abstractmethod
from asyncio import AbstractEventLoop, get_running_loop
from kikiutils.aes import AesCrypt
from kikiutils.time import now_time_utc
from kikiutils.typehint import P, T
from typing import Any, Callable, Coroutine, Optional, Type
from uuid import uuid1


class BaseServiceWebsocketConnection:
    code: str = ''

    def __init__(self, aes: AesCrypt, extra_headers: dict, name: str, request, websocket):
        self._aes = aes
        self.alive = False
        self.extra_headers = extra_headers
        self.ip = self._get_ip(request)
        self.name = name
        self.request = request
        self.time: int = now_time_utc()
        self.uuid = uuid1()
        self.ws = websocket

    @abstractmethod
    def _get_ip(self, rq):
        return ''

    @abstractmethod
    async def emit(self, event: str, *args, **kwargs):
        await self.send(self._aes.encrypt([event, args, kwargs]))

    @abstractmethod
    async def recv_data(self) -> list:
        return []


class BaseServiceWebsockets:
    _connection_class: Type[BaseServiceWebsocketConnection]
    need_accept = False

    def __init__(self, aes: AesCrypt, service_name: str, loop: Optional[AbstractEventLoop] = None):
        self._aes = aes
        self._loop = loop or get_running_loop()
        self.connections: dict[str, Type[BaseServiceWebsocketConnection]] = {}
        self.event_handlers: dict[str, Callable[..., Coroutine]] = {}
        self.service_name = service_name

    @abstractmethod
    def _add_connection(self, name: str, connection: Type[BaseServiceWebsocketConnection]):
        self.connections[name] = connection

    @abstractmethod
    def _del_connection(self, name: str):
        self.connections.pop(name, None)

    @abstractmethod
    async def _listen(self, connection: Type[BaseServiceWebsocketConnection]):
        while True:
            event, args, kwargs = await connection.recv_data()

            if handler := self.event_handlers.get(event):
                self._loop.create_task(handler(connection, *args, **kwargs))

    @abstractmethod
    async def accept_and_listen(
        self,
        name: str,
        request,
        websocket,
        extra_headers: dict = {},
        on_accept: Optional[Callable[[BaseServiceWebsocketConnection], Coroutine[Any, Any, None]]] = None
    ):
        if self.need_accept:
            await websocket.accept()

        connection = None

        try:
            connection = self._connection_class(
                self._aes,
                extra_headers,
                name,
                request,
                websocket
            )

            data = await connection.recv_data()

            if data[0] != 'init' or 'code' not in data[2]:
                raise ValueError('')

            connection.alive = True
            connection.code = data[2]['code']
            self._add_connection(name, connection)

            if on_accept:
                self._loop.create_task(on_accept(connection))

            await self._listen(connection)
        except:
            pass

        if connection:
            connection.alive = False

            if name in self.connections and connection.uuid == self.connections[name].uuid:
                self._del_connection(name)

    @abstractmethod
    async def emit_to_all(self, event: str, *args, **kwargs):
        data = self._aes.encrypt([event, args, kwargs])

        for connection in self.connections.values():
            self._loop.create_task(connection.send(data))

    @abstractmethod
    async def emit_to_connection(self, connection: Type[BaseServiceWebsocketConnection], event: str, *args, **kwargs):
        data = self._aes.encrypt([event, args, kwargs])
        await connection.send(data)

    @abstractmethod
    async def emit_to_name(self, name: str, event: str, *args, **kwargs):
        if connection := self.connections.get(name):
            await self.emit_to_connection(connection, event, *args, **kwargs)

    @abstractmethod
    def get_connection(self, name):
        return self.connections.get(name)

    @abstractmethod
    def on(self, event: str):
        """Register event handler."""

        def decorator(view_func: Callable[P, Coroutine[Any, Any, T]]):
            self.event_handlers[event] = view_func
            return view_func
        return decorator
