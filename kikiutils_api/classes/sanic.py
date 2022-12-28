from kikiutils.aes import AesCrypt
from sanic import Request
from sanic.server.websockets.connection import WebSocketConnection

from . import BaseServiceWebsockets


class ServiceWebsocketConnection:
    code: str = ''

    def __init__(
        self,
        aes: AesCrypt,
        extra_headers: dict,
        ip: str,
        name: str,
        websocket: WebSocketConnection
    ):
        self.aes = aes
        self.extra_headers = extra_headers
        self.ip = ip
        self.name = name
        self.ws = websocket

    async def emit(self, event: str, *args, **kwargs):
        await self.send(self.aes.encrypt([event, args, kwargs]))

    async def send(self, data: bytes | str):
        await self.ws.send(data)

    async def recv_data(self) -> list:
        return self.aes.decrypt(await self.ws.recv())


class ServiceWebsockets(BaseServiceWebsockets):
    connections: dict[str, ServiceWebsocketConnection]

    def __init__(self, aes: AesCrypt, service_name: str):
        super().__init__(aes, service_name)

    async def accept_and_listen(
        self,
        rq: Request,
        name: str,
        websocket: WebSocketConnection,
        extra_headers: dict = {}
    ):
        try:
            connection = ServiceWebsocketConnection(
                self.aes,
                extra_headers,
                rq.remote_addr,
                name,
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
            await connection.send(data)

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
