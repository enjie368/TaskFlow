'''Redis 版登录守卫'''
from redis.asyncio import Redis

from app.application.common.exception import RateLimitError
from app.application.common.login_guard import LoginAttemptGuard

MAX_ATTEMPTS = 5      # 连续失败阈值
LOCK_SECONDS = 600    # 锁 10 分钟

class RedisLoginAttemptGuard(LoginAttemptGuard):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def ensure_allowed(self, username: str) -> None:
        if await self.redis.exists(f"login:lock:{username}"):
            raise RateLimitError()

    async def record_failure(self, username: str) -> None:
        fail_key = f"login:fail:{username}"
        count = await self.redis.incr(fail_key)          # 原子 +1，不存在则建为 1
        if count == 1:
            await self.redis.expire(fail_key, 1800)      # 计数器 30 分钟没动静自动清
        if count >= MAX_ATTEMPTS:
            await self.redis.set(f"login:lock:{username}", "1", ex=LOCK_SECONDS)
            await self.redis.delete(fail_key)            # 上锁后计数器使命完成

    async def reset(self, username: str) -> None:
        await self.redis.delete(f"login:fail:{username}")
        await self.redis.delete(f"login:lock:{username}")
