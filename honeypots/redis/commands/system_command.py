from loguru import logger

from honeypots.redis.command import RedisBaseCommand, ERROR_ARGUMENT

class CommandAuth(RedisBaseCommand):
    async def execute(self):
        if len(self.args) == 1:
            username, password = None, self.args[0]
        elif len(self.args) == 2:
            username, password = self.args
        else:
            await self.protocol.send_data(ERROR_ARGUMENT.format("auth"))
            return
        logger.info("收到身份验证信息: {} {}".format(username, password))
        if username or password:  # 不让填账号密码认证
            await self.protocol.send_data(b"-ERR AUTH <username> called without any password configured for the user, or for the default user. Are you sure your configuration is correct?")


class CommandInfo(RedisBaseCommand):
    async def execute(self):
        info = [
            "# Server",
            "redis_version:6.2.6",
            "redis_git_sha1:00000000",
            "redis_git_dirty:0",
            "redis_build_id:0",
            "redis_mode:standalone",
            "os:Linux 4.15.0-1043-aws x86_64",
            "arch_bits:64",
            "multiplexing_api:epoll",
            "atomicvar_api:atomic-builtin",
            "gcc_version:7.5.0",
            "process_id:1",
            "run_id:random_run_id",
            "tcp_port:6379",
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
        info_string = "\r\n".join(info)
        await self.protocol.send_data(self.protocol.format_bulk_string(info_string))


class CommandPing(RedisBaseCommand):
    async def execute(self):
        await self.protocol.send_data(self.protocol.format_simple_string("PONG"))


class CommandClient(RedisBaseCommand):
    async def execute(self):
        if len(self.args) == 0:
            await self.protocol.send_data(ERROR_ARGUMENT.format("client"))
            return
        if self.args[0].lower() == "setname":
            if len(self.args[1:]) % 2 != 0:
                await self.protocol.send_data(ERROR_ARGUMENT.format("client"))
                return
            set_client_info = dict(zip(self.args[1:][::2], self.args[1:][1::2]))
            logger.info(f"收到客户端信息: setname {set_client_info}")
            await self.protocol.send_data(self.protocol.format_simple_string("OK"))
        else:
            await self.protocol.send_data(self.protocol.format_simple_string("OK"))


commands = {
    "auth": CommandAuth,
    "info": CommandInfo,
    "ping": CommandPing,
    "client": CommandClient
}