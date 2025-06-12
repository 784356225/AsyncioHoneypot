#!/usr/bin/env python3
"""
AsyncioHoneypot - 基于asyncio的低交互蜜罐

主程序入口，根据配置文件启动蜜罐服务
"""

import sys
from pathlib import Path

import asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import SystemConfig
from tools.logger import setup_logger
from honeypots.redis.factory import RedisServer


async def run_honeypot():
    """运行所有蜜罐服务"""
    # 创建任务列表
    tasks = [
        RedisServer("0.0.0.0", 6379).start()
    ]

    # 等待所有任务完成
    await asyncio.gather(*tasks)


def main():
    """主函数"""
    # 初始化日志输出
    setup_logger(
        log_level=SystemConfig.log_level,
        log_dir=SystemConfig.log_dir,
        enable_console=SystemConfig.enable_console_log
    )

    # 运行所有任务
    asyncio.run(run_honeypot())


if __name__ == "__main__":
    main()