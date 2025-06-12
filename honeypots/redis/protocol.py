"""
Redis协议层

处理Redis协议解析和响应格式化
"""

from typing import List, Optional, Union
from tools.logger import get_logger


class RedisProtocol:
    """Redis协议处理器"""

    def __init__(self):
        self.logger = get_logger()
    
    def parse_command(self, data: bytes) -> Optional[List[str]]:
        """
        解析Redis命令
        
        Redis协议格式:
        *<参数数量>\r\n
        $<参数长度>\r\n
        <参数内容>\r\n
        ...
        """
        try:
            lines = data.split(b'\r\n')
            if not lines or not lines[0].startswith(b'*'):
                # 简单命令格式 (如 "AUTH password")
                return self._parse_simple_command(data)
            
            # 数组格式命令
            return self._parse_array_command(lines)
            
        except Exception as e:
            self.logger.error(f"解析命令时发生错误: {e}")
            return None
    
    def _parse_simple_command(self, data: bytes) -> Optional[List[str]]:
        """解析简单命令格式"""
        try:
            command_str = data.decode('utf-8').strip()
            if not command_str:
                return None
            return command_str.split()
        except UnicodeDecodeError:
            self.logger.warning("命令包含非UTF-8字符")
            return None
    
    def _parse_array_command(self, lines: List[bytes]) -> Optional[List[str]]:
        """解析数组格式命令"""
        try:
            if len(lines) < 1:
                return None
            
            # 解析参数数量
            arg_count_line = lines[0]
            if not arg_count_line.startswith(b'*'):
                return None
            
            arg_count = int(arg_count_line[1:])
            if arg_count <= 0:
                return None
            
            args = []
            line_idx = 1
            
            for i in range(arg_count):
                if line_idx >= len(lines):
                    return None
                
                # 解析参数长度
                length_line = lines[line_idx]
                if not length_line.startswith(b'$'):
                    return None
                
                arg_length = int(length_line[1:])
                line_idx += 1
                
                if line_idx >= len(lines):
                    return None
                
                # 解析参数内容
                arg_content = lines[line_idx]
                if len(arg_content) != arg_length:
                    return None
                
                args.append(arg_content.decode('utf-8'))
                line_idx += 1
            
            return args
            
        except (ValueError, UnicodeDecodeError, IndexError) as e:
            self.logger.error(f"解析数组命令时发生错误: {e}")
            return None
    
    def format_simple_string(self, message: str) -> bytes:
        """格式化简单字符串响应 (+OK\r\n)"""
        return f"+{message}\r\n".encode('utf-8')
    
    def format_error(self, error_type: str, message: str) -> bytes:
        """格式化错误响应 (-ERR message\r\n)"""
        return f"-{error_type} {message}\r\n".encode('utf-8')
    
    def format_integer(self, value: int) -> bytes:
        """格式化整数响应 (:123\r\n)"""
        return f":{value}\r\n".encode('utf-8')
    
    def format_bulk_string(self, data: Optional[str]) -> bytes:
        """格式化批量字符串响应"""
        if data is None:
            return b"$-1\r\n"  # NULL
        
        data_bytes = data.encode('utf-8')
        return f"${len(data_bytes)}\r\n".encode('utf-8') + data_bytes + b"\r\n"
    
    def format_array(self, items: Optional[List[Union[str, int, None]]]) -> bytes:
        """格式化数组响应"""
        if items is None:
            return b"*-1\r\n"  # NULL数组
        
        result = f"*{len(items)}\r\n".encode('utf-8')
        
        for item in items:
            if isinstance(item, str):
                result += self.format_bulk_string(item)
            elif isinstance(item, int):
                result += self.format_integer(item)
            elif item is None:
                result += self.format_bulk_string(None)
            else:
                result += self.format_bulk_string(str(item))
        
        return result


class RedisCommandParser:
    """Redis命令解析器"""
    
    def __init__(self, transport, protocol: RedisProtocol):
        self.transport = transport
        self.protocol = protocol
        self.logger = get_logger()
    
    async def read_command(self) -> Optional[List[str]]:
        """读取并解析一个完整的Redis命令"""
        try:
            # 读取第一行
            first_line = await self.transport.read_line()
            if not first_line:
                return None
            
            if first_line.startswith(b'*'):
                # 数组格式命令
                return await self._read_array_command(first_line)
            else:
                # 简单命令格式
                return self.protocol.parse_command(first_line)
                
        except Exception as e:
            self.logger.error(f"读取命令时发生错误: {e}")
            return None
    
    async def _read_array_command(self, first_line: bytes) -> Optional[List[str]]:
        """读取数组格式命令"""
        try:
            # 解析参数数量
            arg_count = int(first_line[1:])
            if arg_count <= 0:
                return None
            
            args = []
            
            for i in range(arg_count):
                # 读取参数长度行
                length_line = await self.transport.read_line()
                if not length_line or not length_line.startswith(b'$'):
                    return None
                
                arg_length = int(length_line[1:])
                if arg_length < 0:
                    args.append(None)
                    continue
                
                # 读取参数内容
                arg_data = await self.transport.read_bulk_string(arg_length)
                if arg_data is None:
                    return None
                
                args.append(arg_data.decode('utf-8'))
            
            return args
            
        except (ValueError, UnicodeDecodeError) as e:
            self.logger.error(f"读取数组命令时发生错误: {e}")
            return None
