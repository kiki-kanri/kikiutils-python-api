from asyncio import AbstractEventLoop, CancelledError, get_running_loop, sleep, Task
from kikiutils.aes import AesCrypt
from kikiutils.log import logger
from kikiutils.string import random_str
from kikiutils.typehint import P, T
from typing import Any, Callable, Coroutine, Optional
from websockets.legacy.client import Connect


class WebsocketClient:
    _check_task: Task
    _listen_task: Task
    code: str

    def __init__(
        self,
        aes: AesCrypt,
        name: str,
        url: str,
        check_interval: int = 3,
        headers: dict = {},
        emit_raise_exception: bool = False,
        loop: Optional[AbstractEventLoop] = None
    ):
        self._aes = aes
        self._emit_raise_exception = emit_raise_exception
        self._loop = loop or get_running_loop()
        self.check_interval = check_interval
        self.code = random_str()
        self.connect_kwargs = {
            'extra_headers': {
                'extra-info': aes.encrypt(headers)
            },
            'ping_interval': None,
            'uri': url
        }

        self.disconnecting = False
        self.event_handlers: dict[str, Callable[..., Coroutine]] = {}
        self.name = name

    async def _check(self):
        while True:
            try:
                await sleep(self.check_interval)
                await self.ws.ping()
            except CancelledError:
                break
            except:
                self._listen_task.cancel()

                try:
                    await self.ws.close()
                except:
                    pass

                return self._loop.create_task(self.wait_connect_success())

    async def _listen(self):
        while True:
            event, args, kwargs = self._aes.decrypt(await self.ws.recv())

            if handler := self.event_handlers.get(event):
                self._loop.create_task(handler(*args, **kwargs))

    async def connect(self):
        if self.disconnecting:
            return

        self.ws = await Connect(**self.connect_kwargs)
        await self.emit('init', code=self.code)
        self._check_task = self._loop.create_task(self._check())
        self._listen_task = self._loop.create_task(self._listen())
        logger.success('Websocket success connected.')

    async def disconnect(self):
        self.disconnecting = True
        self._check_task.cancel()
        self._listen_task.cancel()
        await self.ws.close()
        self.disconnecting = False

    async def emit(self, event: str, *args, **kwargs):
        if self._emit_raise_exception:
            await self.ws.send(self._aes.encrypt([event, args, kwargs]))
        else:
            try:
                await self.ws.send(self._aes.encrypt([event, args, kwargs]))
            except:
                return False

        return True

    def on(self, event: str):
        """Register event handler."""

        def decorator(view_func: Callable[P, Coroutine[Any, Any, T]]):
            self.event_handlers[event] = view_func
            return view_func
        return decorator

    async def wait_connect_success(self):
        """Wait for connect success."""

        while not self.disconnecting:
            try:
                await self.connect()
                break
            except KeyboardInterrupt:
                exit()
            except:
                logger.error('Websocket connect error!')
                await sleep(1)
