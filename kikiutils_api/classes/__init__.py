from abc import abstractmethod
from asyncio import create_task, Future
from functools import wraps
from kikiutils.aes import AesCrypt
from kikiutils.time import now_time_utc
from typing import Callable, Coroutine, Optional, Type
from uuid import uuid1


class BaseServiceWebsocketConnection:
    code: str = ''

    def __init__(
        self,
        aes: AesCrypt,
        extra_headers: dict,
        name: str,
        request,
        websocket
    ):
        self.aes = aes
        self.extra_headers = extra_headers
        self.ip = self._get_ip(request)
        self.name = name
        self.request = request
        self.time: int = now_time_utc()
        self.uuid = uuid1()
        self.ws = websocket

    def _get_ip(self, rq):
        return ''

    @abstractmethod
    async def emit(self, event: str, *args, **kwargs):
        await self.send(self.aes.encrypt([event, args, kwargs]))

    @abstractmethod
    async def recv_data(self) -> list:
        return []


class BaseServiceWebsockets:
    _connection_class: Type[BaseServiceWebsocketConnection]
    need_accept = False

    def __init__(self, aes: AesCrypt, service_name: str):
        self.aes = aes
        self.connections: dict[
            str,
            Type[BaseServiceWebsocketConnection]
        ] = {}

        self.event_handlers: dict[str, Callable[..., Coroutine]] = {}
        self.service_name = service_name
        self.waiting_events: dict[str, dict[str, Future]] = {}

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

            if event in self.event_handlers:
                create_task(
                    self.event_handlers[event](connection, *args, **kwargs)
                )

            if event in self.waiting_events:
                uuid: Optional[str] = kwargs.get('__wait_event_uuid')

                if uuid and uuid in self.waiting_events[event]:
                    self.waiting_events[event][uuid].set_result((args, kwargs))
                    self.waiting_events[event].pop(uuid, None)

    @abstractmethod
    async def accept_and_listen(
        self,
        name: str,
        request,
        websocket,
        extra_headers: dict = {}
    ):
        if self.need_accept:
            await websocket.accept()

        connection = None

        try:
            connection = self._connection_class(
                self.aes,
                extra_headers,
                name,
                request,
                websocket
            )

            data = await connection.recv_data()

            if data[0] != 'init' or 'code' not in data[2]:
                raise ValueError('')

            connection.code = data[2]['code']
            self._add_connection(name, connection)
            await self._listen(connection)
        except:
            pass

        if connection and name in self.connections and connection.uuid == self.connections[name].uuid:
            self._del_connection(name)

    @abstractmethod
    async def emit_and_wait_event(
        self,
        name: str,
        event: str,
        wait_event: str,
        *args,
        **kwargs
    ):
        uuid = uuid1().hex
        kwargs['__wait_event_uuid'] = uuid

        if wait_event in self.waiting_events:
            self.waiting_events[wait_event][uuid] = Future()
        else:
            self.waiting_events[wait_event] = {uuid: Future()}

        await self.emit_to_name(name, event, *args, **kwargs)
        return await self.waiting_events[wait_event][uuid]

    @abstractmethod
    async def emit_to_all(self, event: str, *args, **kwargs):
        data = self.aes.encrypt([event, args, kwargs])

        for connection in self.connections.values():
            create_task(connection.send(data))

    @abstractmethod
    async def emit_to_name(
        self,
        name: str,
        event: str,
        *args,
        **kwargs
    ):
        if connection := self.connections.get(name):
            data = self.aes.encrypt([event, args, kwargs])
            await connection.send(data)

    @abstractmethod
    def get_connection(self, name):
        return self.connections.get(name)

    @abstractmethod
    def on(self, event: str):
        """Register event handler."""

        def decorator(view_func):
            @wraps(view_func)
            async def wrapped_view(*args, **kwargs):
                await view_func(*args, **kwargs)
            self.event_handlers[event] = wrapped_view
            return wrapped_view
        return decorator
