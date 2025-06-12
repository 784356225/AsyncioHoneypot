"""
包含统一的异常处理逻辑，便于集中管理
"""

class ConnectDone(Exception):
    """连接完毕，正常断开"""
    pass