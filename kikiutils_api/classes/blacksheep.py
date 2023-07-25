from blacksheep import Request, WebSocket
from typing import Union

from ..utils.blacksheep import get_ip
from . import BaseServiceWebsockets, BaseServiceWebsocketConnection


class ServiceWebsocketConnection(BaseServiceWebsocketConnection):
    rq: Request
    ws: WebSocket

    def _get_ip(self, rq: Request):
        return get_ip(rq)

    async def send(self, data: Union[bytes, str]):
        if isinstance(data, bytes):
            return await self.ws.send_bytes(data)
        await self.ws.send_text(data)

    async def recv_data(self) -> list:
        return self._aes.decrypt(await self.ws.receive_text())


class ServiceWebsockets(BaseServiceWebsockets):
    _connection_class = ServiceWebsocketConnection
    connections: dict[str, ServiceWebsocketConnection]
    need_accept = True
