"""
日志工具模块

使用loguru实现统一的日志管理
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
from loguru import logger


class HoneypotLogger:
    """蜜罐日志记录器"""
    
    def __init__(self, service_name: str, log_dir: str = "logs"):
        self.service_name = service_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # JSON日志文件
        self.json_log_file = self.log_dir / f"{service_name}_attacks.jsonl"
        
        # 为当前服务创建专用logger
        self.logger = logger.bind(service=service_name)
    
    def log_connection(self, client_ip: str, client_port: int):
        """记录客户端连接"""
        self.logger.info(f"新连接: {client_ip}:{client_port}")
        
        self._write_json_log({
            "timestamp": datetime.now().isoformat(),
            "event_type": "connection",
            "service": self.service_name,
            "client_ip": client_ip,
            "client_port": client_port
        })
    
    def log_auth_attempt(self, client_ip: str, client_port: int, 
                        username: Optional[str] = None, password: Optional[str] = None, 
                        success: bool = False):
        """记录认证尝试"""
        status = "成功" if success else "失败"
        auth_info = []
        
        if username:
            auth_info.append(f"用户名: {username}")
        if password:
            auth_info.append(f"密码: {password}")
        
        auth_display = ", ".join(auth_info) if auth_info else "(空认证信息)"
        
        self.logger.warning(
            f"认证尝试 {status}: {client_ip}:{client_port} - {auth_display}"
        )
        
        self._write_json_log({
            "timestamp": datetime.now().isoformat(),
            "event_type": "auth_attempt",
            "service": self.service_name,
            "client_ip": client_ip,
            "client_port": client_port,
            "username": username,
            "password": password,
            "success": success
        })
    
    def log_command(self, client_ip: str, client_port: int, 
                   command: str, args: list = None):
        """记录执行的命令"""
        args_str = ' '.join(args) if args else ''
        self.logger.info(
            f"命令执行: {client_ip}:{client_port} - {command} {args_str}".strip()
        )
        
        self._write_json_log({
            "timestamp": datetime.now().isoformat(),
            "event_type": "command",
            "service": self.service_name,
            "client_ip": client_ip,
            "client_port": client_port,
            "command": command,
            "args": args or []
        })
    
    def log_invalid_command(self, client_ip: str, client_port: int, 
                           raw_data: Union[bytes, str]):
        """记录无效命令"""
        if isinstance(raw_data, bytes):
            try:
                data_str = raw_data.decode('utf-8', errors='replace')
            except:
                data_str = str(raw_data)
        else:
            data_str = str(raw_data)
        
        self.logger.warning(
            f"无效命令: {client_ip}:{client_port} - {data_str[:100]}"
        )
        
        self._write_json_log({
            "timestamp": datetime.now().isoformat(),
            "event_type": "invalid_command",
            "service": self.service_name,
            "client_ip": client_ip,
            "client_port": client_port,
            "raw_data": data_str[:200]  # 限制长度
        })
    
    def log_disconnect(self, client_ip: str, client_port: int, 
                      session_duration: float):
        """记录客户端断开连接"""
        self.logger.info(
            f"连接断开: {client_ip}:{client_port} - 会话时长: {session_duration:.2f}秒"
        )
        
        self._write_json_log({
            "timestamp": datetime.now().isoformat(),
            "event_type": "disconnect",
            "service": self.service_name,
            "client_ip": client_ip,
            "client_port": client_port,
            "session_duration": session_duration
        })
    
    def log_error(self, client_ip: str, client_port: int, 
                 error_type: str, error_message: str):
        """记录错误"""
        self.logger.error(
            f"错误: {client_ip}:{client_port} - {error_type}: {error_message}"
        )
        
        self._write_json_log({
            "timestamp": datetime.now().isoformat(),
            "event_type": "error",
            "service": self.service_name,
            "client_ip": client_ip,
            "client_port": client_port,
            "error_type": error_type,
            "error_message": error_message
        })
    
    def log_attack_pattern(self, client_ip: str, pattern_type: str, 
                          details: Dict[str, Any]):
        """记录攻击模式"""
        self.logger.warning(
            f"检测到攻击模式: {client_ip} - {pattern_type}"
        )
        
        self._write_json_log({
            "timestamp": datetime.now().isoformat(),
            "event_type": "attack_pattern",
            "service": self.service_name,
            "client_ip": client_ip,
            "pattern_type": pattern_type,
            "details": details
        })
    
    def _write_json_log(self, data: Dict[str, Any]):
        """写入JSON格式日志"""
        try:
            with open(self.json_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"写入JSON日志失败: {e}")


def setup_logger(log_level: str = "INFO", log_dir: str = "logs", 
                enable_console: bool = True, enable_file: bool = True):
    """
    设置全局日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_dir: 日志目录
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
    """
    # 移除默认handler
    logger.remove()
    
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 日志格式
    log_format = (
        "[<green>{time:YYYY-MM-DD HH:mm:ss,SSS}</green>]"
        "[<cyan>{name}</cyan>,<cyan>{line}</cyan>]"
        "[<level>{level}</level>] "
        "<level>{message}</level>"
    )
    
    # 控制台输出
    if enable_console:
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            colorize=True
        )
    
    # 文件输出 - 主日志文件
    if enable_file:
        logger.add(
            log_path / "honeypot.log",
            format=log_format,
            level=log_level,
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            enqueue=True  # 异步写入
        )
        
        # 错误日志文件
        logger.add(
            log_path / "error.log",
            format=log_format,
            level="ERROR",
            rotation="5 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            enqueue=True
        )
    
    # 绑定默认service
    return logger


def get_logger():
    """
    获取指定服务的logger
    
    Args:
        service_name: 服务名称
        
    Returns:
        绑定了服务名的logger实例
    """
    return logger


# 创建全局蜜罐日志记录器实例
_honeypot_loggers = {}


def get_honeypot_logger(service_name: str, log_dir: str = "logs") -> HoneypotLogger:
    """
    获取蜜罐日志记录器实例
    
    Args:
        service_name: 服务名称
        log_dir: 日志目录
        
    Returns:
        HoneypotLogger实例
    """
    if service_name not in _honeypot_loggers:
        _honeypot_loggers[service_name] = HoneypotLogger(service_name, log_dir)
    return _honeypot_loggers[service_name]
