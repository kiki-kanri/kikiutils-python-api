from asyncio import AbstractEventLoop, get_event_loop, sleep, Task
from functools import wraps
from kikiutils.aes import AesCrypt
from kikiutils.string import random_str
from typing import Callable, Coroutine
from websockets.legacy.client import Connect


class WebsocketClient:
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

        self.event_handlers: dict[
            str,
            Callable[..., Coroutine]
        ] = {}

        self.name = name

    async def _check(self):
        try:
            await sleep(self.check_interval)
            await self.ws.ping()
            self._create_task(self._check())
        except:
            self._listen_task.cancel()

            while True:
                await sleep(1)

                try:
                    await self.connect()
                    break
                except:
                    pass

    def _create_task(self, coro: Coroutine):
        if self.loop is None:
            self.loop = get_event_loop()
        return self.loop.create_task(coro)

    async def _listen(self):
        while True:
            event, args, kwargs = self.aes.decrypt(await self.ws.recv())

            if event in self.event_handlers:
                self._create_task(self.event_handlers[event](*args, **kwargs))

    async def connect(self):
        self.ws = await Connect(**self.connect_kwargs)
        await self.send('init', code=self.code)
        self._create_task(self._check())
        self._listen_task = self._create_task(self._listen())

    def on(self, event: str):
        """Register event handler."""

        def decorator(view_func):
            @wraps(view_func)
            async def wrapped_view(*args, **kwargs):
                await view_func(*args, **kwargs)
            self.event_handlers[event] = wrapped_view
            return wrapped_view
        return decorator

    async def send(self, event: str, *args, **kwargs):
        await self.ws.send(self.aes.encrypt([event, args, kwargs]))
