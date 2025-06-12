import asyncio
import traceback
from abc import ABC, abstractmethod
from loguru import logger
from tools.exception import ConnectDone


class BaseTransport(ABC):
    """基础传输层处理器，所有传输层实现的基类"""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.client_address = writer.get_extra_info('peername')

    @abstractmethod
    async def data_received(self, data: bytes):
        """客户端数据接收"""
        pass

    async def write_data(self, data: bytes) -> bool:
        """发送数据"""
        try:
            self.writer.write(data)
            await self.writer.drain()
            return True
        except:
            logger.error(f"发送数据时发生错误: {traceback.format_exc()}")
            return False

    async def connection_lost(self, reason: Exception = ConnectDone):
        """连接断开"""
        logger.info(f"{self.client_address[0]}:{self.client_address[1]} Connection lost: {reason}")
        await self.close()

    async def close(self):
        """关闭连接"""
        self.writer.close()
