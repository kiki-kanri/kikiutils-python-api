from asyncio import create_task
from blacksheep import WebSocket
from functools import wraps
from typing import Callable, Coroutine

from kikiutils.aes import AesCrypt


class ServiceWebsocketConnection:
    code = None

    def __init__(self, aes: AesCrypt, websocket: WebSocket):
        self.aes = aes
        self.ws = websocket

    async def send(self, event: str, *args, **kwargs):
        await self.ws.send_bytes(
            self.aes.encrypt([
                event,
                args,
                kwargs
            ], True)
        )

    async def recv_data(self):
        return self.aes.decrypt(await self.ws.receive_bytes())


class ServiceWebsockets:
    def __init__(self, aes: AesCrypt):
        self.aes = aes
        self.event_handlers: dict[
            str,
            Callable[..., Coroutine]
        ] = {}

        self.websockets: dict[
            str,
            dict[str, ServiceWebsocketConnection]
        ] = {}

    async def _listen(self, ws_connection: ServiceWebsocketConnection):
        while True:
            event, args, kwargs = await ws_connection.recv_data()

            if event in self.event_handlers:
                create_task(
                    self.event_handlers[event](
                        ws_connection,
                        *args,
                        **kwargs
                    )
                )

    # Connection

    async def accept_and_listen(self, code: str, websocket: WebSocket):
        await websocket.accept()
        data = None
        ws_connection = ServiceWebsocketConnection(self.aes, websocket)

        try:
            data = await ws_connection.recv_data()

            if data[0] != 'init' or 'code' not in data[2]:
                raise ValueError('')

            ws_connection.code = data[2]['code']
            self.add_websocket(code, ws_connection)
            await self._listen(ws_connection)
        except:
            pass

        if data and ws_connection.code:
            self.del_websocket(code, ws_connection.code)

    def add_websocket(
        self,
        code: str,
        websocket: ServiceWebsocketConnection
    ):
        """Add connection to connections pool."""

        if code not in self.websockets:
            self.websockets[code] = {websocket.code: websocket}
        else:
            self.websockets[code][websocket.code] = websocket

    def del_websocket(self, code: str, websocket_code: str):
        if self.websockets.get(code):
            self.websockets[code].pop(websocket_code, None)

            if not self.websockets[code]:
                self.websockets.pop(code, None)

    # Event register and listen

    def on(self, event: str):
        """Register event handler."""

        def decorator(view_func):
            @wraps(view_func)
            async def wrapped_view(*args, **kwargs):
                await view_func(*args, **kwargs)
            self.event_handlers[event] = wrapped_view
            return wrapped_view
        return decorator
