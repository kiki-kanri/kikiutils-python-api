from sanic import Request
from sanic.server.websockets.connection import WebSocketConnection
from typing import Union

from . import BaseServiceWebsockets, BaseServiceWebsocketConnection


class ServiceWebsocketConnection(BaseServiceWebsocketConnection):
    rq: Request
    ws: WebSocketConnection

    def _get_ip(self, rq: Request):
        return rq.remote_addr

    async def send(self, data: Union[bytes, str]):
        await self.ws.send(data)

    async def recv_data(self) -> list:
        return self._aes.decrypt(await self.ws.recv())


class ServiceWebsockets(BaseServiceWebsockets):
    _connection_class = ServiceWebsocketConnection
    connections: dict[str, ServiceWebsocketConnection]
