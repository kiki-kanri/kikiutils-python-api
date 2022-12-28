from blacksheep import WebSocket
from kikiutils.aes import AesCrypt

from ..utils.blacksheep import get_ip
from . import BaseServiceWebsockets


class ServiceWebsocketConnection:
    code: str = ''

    def __init__(
        self,
        aes: AesCrypt,
        extra_headers: dict,
        ip: str,
        name: str,
        websocket: WebSocket
    ):
        self.aes = aes
        self.extra_headers = extra_headers
        self.ip = ip
        self.name = name
        self.ws = websocket

    async def emit(self, event: str, *args, **kwargs):
        await self.send_text(self.aes.encrypt([event, args, kwargs]))

    async def send_text(self, text: str):
        await self.ws.send_text(text)

    async def recv_data(self) -> list:
        return self.aes.decrypt(await self.ws.receive_text())


class ServiceWebsockets(BaseServiceWebsockets):
    connections: dict[str, ServiceWebsocketConnection]

    def __init__(self, aes: AesCrypt, service_name: str):
        super().__init__(aes, service_name)

    async def accept_and_listen(
        self,
        name: str,
        websocket: WebSocket,
        extra_headers: dict = {}
    ):
        await websocket.accept()

        try:
            ip = get_ip(websocket)
            connection = ServiceWebsocketConnection(
                self.aes,
                extra_headers,
                name,
                ip,
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

        self._del_connection(name)

    async def emit_to_all(self, event: str, *args, **kwargs):
        data = self.aes.encrypt([event, args, kwargs])

        for connection in self.connections.values():
            await connection.send_text(data)

    async def emit_to_name(
        self,
        name: str,
        event: str,
        *args,
        **kwargs
    ):
        if connection := self.connections.get(name):
            data = self.aes.encrypt([event, args, kwargs])
            await connection.send_text(data)
