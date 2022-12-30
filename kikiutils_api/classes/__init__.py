from abc import abstractmethod
from asyncio import create_task, Future
from functools import wraps
from kikiutils.aes import AesCrypt
from typing import Callable, Coroutine, Optional
from uuid import uuid1


class BaseServiceWebsockets:
    def __init__(self, aes: AesCrypt, service_name: str):
        self.aes = aes
        self.connections = {}
        self.event_handlers: dict[str, Callable[..., Coroutine]] = {}
        self.service_name = service_name
        self.waiting_events: dict[str, dict[str, Future]] = {}

    @abstractmethod
    def _add_connection(self, name: str, connection):
        self.connections[name] = connection

    @abstractmethod
    def _del_connection(self, name: str):
        self.connections.pop(name, None)

    @abstractmethod
    async def _listen(self, connection):
        while True:
            event, args, kwargs = await connection.recv_data()

            if event in self.event_handlers:
                create_task(
                    self.event_handlers[event](
                        connection,
                        *args,
                        **kwargs
                    )
                )

            if event in self.waiting_events:
                uuid: Optional[str] = kwargs.get('__wait_event_uuid')

                if uuid and uuid in self.waiting_events[event]:
                    self.waiting_events[event][uuid].set_result((args, kwargs))
                    self.waiting_events[event].pop(uuid, None)

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
    async def emit_to_name(
        self,
        name: str,
        event: str,
        *args,
        **kwargs
    ):
        pass

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
