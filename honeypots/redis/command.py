from honeypots.redis.protocol import RedisProtocol
from abc import abstractmethod, ABC

ERROR_OPERATION = "-WRONGTYPE Operation against a key holding the wrong kind of value"
ERROR_ARGUMENT = "-ERR wrong number of arguments for '{}' command\r\n"

class RedisBaseCommand(ABC):
    """Redis命令基类，用于存放命令类共用的类方法，所有的命令类必须继承自这个类"""
    def __init__(self, protocol: RedisProtocol, args: list[str]):
        self.protocol = protocol
        self.args = args

    @abstractmethod
    async def execute(self):
        """命令运行的主要入口"""
        pass
