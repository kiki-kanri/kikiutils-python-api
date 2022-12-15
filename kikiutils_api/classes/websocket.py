from asyncio import AbstractEventLoop, Future, get_event_loop, sleep, Task
from functools import wraps
from kikiutils.aes import AesCrypt
from kikiutils.string import random_str
from typing import Callable, Coroutine
from uuid import uuid1
from websockets.legacy.client import Connect


class WebsocketClient:
    _check_task: Task
    _listen_task: Task
    code: str
    loop: AbstractEventLoop = None

    def __init__(
        self,
        aes: AesCrypt,
        name: str,
        url: str,
        check_interval: int = 3,
        headers: dict = {}
    ):
        self.aes = aes
        self.check_interval = check_interval
        self.code = random_str()
        self.connect_kwargs = {
            'extra_headers': {
                'extra-info': aes.encrypt(headers)
            },
            'ping_interval': None,
            'uri': url
        }

        self.event_handlers: dict[str, Callable[..., Coroutine]] = {}
        self.name = name
        self.waiting_events: dict[str, dict[str, Future]] = {}

    async def _check(self):
        try:
            await sleep(self.check_interval)
            await self.ws.ping()
            self._check_task = self._create_task(self._check())
        except:
            self._listen_task.cancel()
            await self.wait_connect_success()

    def _create_task(self, coro: Coroutine):
        if self.loop is None:
            self.loop = get_event_loop()
        return self.loop.create_task(coro)

    async def _listen(self):
        while True:
            event, args, kwargs = self.aes.decrypt(await self.ws.recv())

            if event in self.event_handlers:
                self._create_task(self.event_handlers[event](*args, **kwargs))

            if event in self.waiting_events:
                uuid: int | None = kwargs.get('__wait_event_uuid')

                if uuid and uuid in self.waiting_events[event]:
                    self.waiting_events[event][uuid].set_result((args, kwargs))
                    self.waiting_events[event].pop(uuid, None)

    async def connect(self):
        self.ws = await Connect(**self.connect_kwargs)
        await self.emit('init', code=self.code)
        self._check_task = self._create_task(self._check())
        self._listen_task = self._create_task(self._listen())

    async def disconnect(self):
        self._check_task.cancel()
        self._listen_task.cancel()
        await self.ws.close()

    async def emit(self, event: str, *args, **kwargs):
        await self.ws.send(self.aes.encrypt([event, args, kwargs]))

    async def emit_and_wait_event(
        self,
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

        await self.emit(event, *args, **kwargs)
        return await self.waiting_events[wait_event][uuid]

    def on(self, event: str):
        """Register event handler."""

        def decorator(view_func):
            @wraps(view_func)
            async def wrapped_view(*args, **kwargs):
                await view_func(*args, **kwargs)
            self.event_handlers[event] = wrapped_view
            return wrapped_view
        return decorator

    async def wait_connect_success(self):
        """Wait for connect success."""

        while True:
            try:
                await self.connect()
                break
            except KeyboardInterrupt:
                exit()
            except:
                await sleep(1)
