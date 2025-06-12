"""
AsyncioHoneypot 配置文件

所有蜜罐服务的配置参数
"""

from typing import Dict, Any


class SystemConfig:
    """系统配置类"""
    honeypot_name: str = 'AsyncioHoneypot'
    honeypot_version: str = '0.0.1'
    log_level: str = 'DEBUG'
    enable_console_log: bool = True
    log_dir: str = 'logs'
    host: str = '0.0.0.0'


class RedisHoneypotConfig:
    """Redis蜜罐配置类"""
    port: int = 6379
    max_connections: int = 100
    redis_version: str = '6.2.6'
