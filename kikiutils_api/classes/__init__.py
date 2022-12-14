from abc import abstractmethod
from asyncio import create_task
from functools import wraps
from kikiutils.aes import AesCrypt
from typing import Callable, Coroutine


class BaseServiceWebsockets:
    def __init__(self, aes: AesCrypt, service_name: str):
        self.aes = aes
        self.connections = {}
        self.event_handlers: dict[str, Callable[..., Coroutine]] = {}
        self.service_name = service_name

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
