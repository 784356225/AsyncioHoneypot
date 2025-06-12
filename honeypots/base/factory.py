import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from loguru import logger
from honeypots.base.transport import BaseTransport


class BaseFactory(ABC):
    """基础工厂类，所有工厂的基类"""
    @abstractmethod
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None

    @abstractmethod
    def build_transport(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> BaseTransport:
        """构建传输对象

        Args:
            reader: asyncio.StreamReader
            writer: asyncio.StreamWriter

        Returns:
            BaseTransport实例
        """

    async def connect(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """处理客户端连接, 新连接时会被调用，每个连接都会单独启动这个任务"""
        transport = self.build_transport(reader, writer)
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    await transport.connection_lost()
                    break
                await transport.data_received(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await transport.connection_lost(e)

    async def start(self):
        """启动服务"""
        self.server = await asyncio.start_server(
            self.connect,
            self.host,
            self.port
        )

        addr = self.server.sockets[0].getsockname()
        logger.info(f"服务器启动在 {addr[0]}:{addr[1]}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        """停止服务器"""



