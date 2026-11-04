'''登录尝试守卫——限流的抽象契约，不关心背后是 Redis 还是内存'''
from abc import ABC, abstractmethod

class LoginAttemptGuard(ABC):
    @abstractmethod
    async def ensure_allowed(self, username: str) -> None:
        '''允许登录则什么都不做；被锁则抛 RateLimitError'''

    @abstractmethod
    async def record_failure(self, username: str) -> None:
        '''记一次失败，达到阈值时上锁'''

    @abstractmethod
    async def reset(self, username: str) -> None:
        '''登录成功后清零'''
