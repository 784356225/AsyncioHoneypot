"""
Redis蜜罐传输层

处理TCP连接和基础网络通信
"""

import asyncio
import builtins
from typing import TYPE_CHECKING

from loguru import logger
from honeypots.base.transport import BaseTransport
from honeypots.redis.protocol import RedisProtocol

if TYPE_CHECKING:
    from honeypots.redis.factory import RedisServer


class RedisTransport(BaseTransport):
    """Redis传输层处理器"""

    def __init__(self, factory: 'RedisServer', reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__(reader, writer)
        self.client_host, self.client_port = self.client_address
        self.factory = factory
        self.protocol = RedisProtocol(self)

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
        try:
            command, args = command_list[0], command_list[1:]
        except builtins.IndexError:
            command, args = command_list[0], []

        logger.info(f"解析后的命令: {command_list}")
        command = command.lower()
        command_class = self.factory.commands.get(command)
        if not command_class:
            await self.write_data(self.protocol.format_error("ERR", f"unknown command `{command}`, with args beginning with:{'`{}`'.format(' '.join(args)) if args else ''}"))
        else:
            command_instance = command_class(self.protocol, args)
            await command_instance.execute()
