import asyncio
from typing import Optional, Callable
from loguru import logger

from honeypots.base.factory import BaseFactory
from honeypots.redis.transport import RedisTransport
from honeypots.redis import commands as cmd
from config import RedisHoneypotConfig


class RedisServer(BaseFactory):
    """Redis服务器传输层"""
    commands = {}
    for c in cmd.__all__:
        module = __import__(
            f"honeypots.redis.commands.{c}", globals(), locals(), ["commands"]
        )
        commands.update(module.commands)

    def __init__(self, host: str = '0.0.0.0', port: int = 6379):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.client_handler: Optional[Callable] = None
        self.max_connections = RedisHoneypotConfig.max_connections
        self.active_connections = 0

    def build_transport(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> RedisTransport | None:
        """构建传输对象"""
        transport = RedisTransport(self, reader, writer)
        client_addr = transport.client_address
        logger.info(f"新的客户端连接: {client_addr[0]}:{client_addr[1]}")
        return transport
