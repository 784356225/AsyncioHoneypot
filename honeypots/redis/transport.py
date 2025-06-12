"""
Redis蜜罐传输层

处理TCP连接和基础网络通信
"""

import asyncio
from loguru import logger
from honeypots.base.transport import BaseTransport
from honeypots.redis.protocol import RedisProtocol


class RedisTransport(BaseTransport):
    """Redis传输层处理器"""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__(reader, writer)
        self.protocol = RedisProtocol()

    async def data_received(self, data: bytes):
        """报文数据接收"""
        logger.info(f"收到数据: {data}")
        await self.process_data(data)


    async def write_data(self, data: bytes) -> bool:
        """发送数据"""
        try:
            self.writer.write(data)
            await self.writer.drain()
            return True
        except Exception as e:
            logger.error(f"发送数据时发生错误: {e}")
            return False

    async def process_data(self, data: bytes):
        """处理接收到的数据"""
        command_list = self.protocol.parse_command(data)
        logger.info(f"解析后的命令: {command_list}")
        if command_list[0] == "PING":
            await self.write_data(self.protocol.format_simple_string("PONG"))
        else:
            await self.write_data(self.protocol.format_error("ERR", "unknown command"))
