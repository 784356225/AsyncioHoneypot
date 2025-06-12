"""
Redis命令处理器

处理Redis命令逻辑，特别是AUTH命令
"""

import time
import asyncio
from typing import Optional, Dict, Any
from .protocol import RedisProtocol
from .logger import honeypot_logger


class RedisCommandHandler:
    """Redis命令处理器"""

    def __init__(self, client_ip: str, client_port: int, config: Dict[str, Any] = None):
        self.client_ip = client_ip
        self.client_port = client_port
        self.protocol = RedisProtocol()
        self.authenticated = False
        self.session_start_time = time.time()

        # 使用传入的配置或默认配置
        if config is None:
            from config import get_service_config
            config = get_service_config('redis')

        self.config = config

        # 模拟的Redis配置
        self.redis_config = {
            "requirepass": config.get('fake_password'),
            "version": config.get('redis_version', '6.2.6'),
            "mode": config.get('redis_mode', 'standalone'),
            "port": config.get('port', 6379)
        }

        # 记录连接
        honeypot_logger.log_connection(self.client_ip, self.client_port)
    
    async def handle_command(self, command_parts: list) -> bytes:
        """处理Redis命令"""
        if not command_parts:
            return self.protocol.format_error("ERR", "empty command")

        command = command_parts[0].upper()
        args = command_parts[1:] if len(command_parts) > 1 else []

        # 检查是否记录所有命令
        if self.config.get('log_all_commands', True):
            honeypot_logger.log_command(self.client_ip, self.client_port, command, args)

        # 检查命令是否在支持列表中
        supported_commands = self.config.get('supported_commands', [])
        if supported_commands and command not in supported_commands:
            return await self.handle_unknown_command(command, args)

        # 模拟响应延迟
        response_delay = self.config.get('response_delay', 0)
        if response_delay > 0:
            await asyncio.sleep(response_delay)

        # 根据命令类型分发处理
        if command == "AUTH":
            return await self.handle_auth(args)
        elif command == "PING":
            return await self.handle_ping(args)
        elif command == "INFO":
            return await self.handle_info(args)
        elif command == "SELECT":
            return await self.handle_select(args)
        elif command == "QUIT":
            return await self.handle_quit()
        else:
            return await self.handle_unknown_command(command, args)
    
    async def handle_auth(self, args: list) -> bytes:
        """处理AUTH命令"""
        if len(args) == 0:
            if self.config.get('log_auth_attempts', True):
                honeypot_logger.log_auth_attempt(
                    self.client_ip, self.client_port, password=None, success=False
                )
            return self.protocol.format_error("ERR", "wrong number of arguments for 'auth' command")

        password = args[0]

        # 记录认证尝试
        if self.config.get('log_auth_attempts', True):
            honeypot_logger.log_auth_attempt(
                self.client_ip, self.client_port, password=password, success=False
            )

        # 模拟认证失败（蜜罐总是拒绝认证）
        if self.redis_config["requirepass"] is None:
            # 如果没有设置密码，返回不需要认证的错误
            return self.protocol.format_error("ERR", "Client sent AUTH, but no password is set")
        else:
            # 如果设置了密码，总是返回认证失败
            return self.protocol.format_error("ERR", "invalid password")
    
    async def handle_ping(self, args: list) -> bytes:
        """处理PING命令"""
        if len(args) == 0:
            return self.protocol.format_simple_string("PONG")
        else:
            # 带参数的PING，返回参数
            return self.protocol.format_bulk_string(args[0])
    
    async def handle_info(self, args: list) -> bytes:
        """处理INFO命令"""
        # 模拟Redis INFO响应
        info_data = [
            "# Server",
            f"redis_version:{self.redis_config['version']}",
            "redis_git_sha1:00000000",
            "redis_git_dirty:0",
            "redis_build_id:0",
            f"redis_mode:{self.redis_config['mode']}",
            "os:Linux 4.15.0-1043-aws x86_64",
            "arch_bits:64",
            "multiplexing_api:epoll",
            "atomicvar_api:atomic-builtin",
            "gcc_version:7.5.0",
            "process_id:1",
            "run_id:random_run_id",
            f"tcp_port:{self.redis_config['port']}",
            "uptime_in_seconds:3600",
            "uptime_in_days:0",
            "hz:10",
            "configured_hz:10",
            "lru_clock:123456",
            "executable:/usr/local/bin/redis-server",
            "config_file:",
            "",
            "# Clients",
            "connected_clients:1",
            "client_recent_max_input_buffer:2",
            "client_recent_max_output_buffer:0",
            "blocked_clients:0",
            "",
            "# Memory",
            "used_memory:1048576",
            "used_memory_human:1.00M",
            "used_memory_rss:2097152",
            "used_memory_rss_human:2.00M",
            "used_memory_peak:1048576",
            "used_memory_peak_human:1.00M",
            "",
            "# Stats",
            "total_connections_received:1",
            "total_commands_processed:1",
            "instantaneous_ops_per_sec:0",
            "total_net_input_bytes:14",
            "total_net_output_bytes:0",
            "instantaneous_input_kbps:0.00",
            "instantaneous_output_kbps:0.00",
            "rejected_connections:0",
            "sync_full:0",
            "sync_partial_ok:0",
            "sync_partial_err:0",
            "expired_keys:0",
            "evicted_keys:0",
            "keyspace_hits:0",
            "keyspace_misses:0",
            "pubsub_channels:0",
            "pubsub_patterns:0",
            "latest_fork_usec:0",
            "migrate_cached_sockets:0",
            "slave_expires_tracked_keys:0",
            "active_defrag_hits:0",
            "active_defrag_misses:0",
            "active_defrag_key_hits:0",
            "active_defrag_key_misses:0"
        ]
        
        info_string = "\r\n".join(info_data)
        return self.protocol.format_bulk_string(info_string)
    
    async def handle_select(self, args: list) -> bytes:
        """处理SELECT命令"""
        if len(args) != 1:
            return self.protocol.format_error("ERR", "wrong number of arguments for 'select' command")
        
        try:
            db_index = int(args[0])
            if db_index < 0 or db_index > 15:
                return self.protocol.format_error("ERR", "DB index is out of range")
            
            return self.protocol.format_simple_string("OK")
        except ValueError:
            return self.protocol.format_error("ERR", "value is not an integer or out of range")
    
    async def handle_quit(self) -> bytes:
        """处理QUIT命令"""
        return self.protocol.format_simple_string("OK")
    
    async def handle_unknown_command(self, command: str, args: list) -> bytes:
        """处理未知命令"""
        return self.protocol.format_error(
            "ERR", 
            f"unknown command '{command}', with args beginning with: {', '.join(repr(arg) for arg in args[:3])}"
        )
    
    def get_session_duration(self) -> float:
        """获取会话持续时间"""
        return time.time() - self.session_start_time
