'''Redis 版订单查询缓存'''
import json
from datetime import datetime
from decimal import Decimal

from redis.asyncio import Redis

from app.application.common.order_query_cache import OrderQueryCache
from app.application.user.queries.get_orders import GetOrdersResult, OrderDTO

CACHE_TTL_SECONDS = 60   # 数据 key 的存活时间：兜底保险，就算失效有漏最多脏 1 分钟

class RedisOrderQueryCache(OrderQueryCache):
    '''用 Redis 实现缓存三件套'''

    def __init__(self, redis: Redis):
        '''接收一个 Redis 连接客户端（由组合根 dependency.py 注入）'''
        self.redis = redis

    def _ver_key(self, user_id: int) -> str:
        '''拼版本 key：每个用户一个，记录"当前有效代数"'''
        return f"orders:ver:{user_id}"

    def _data_key(self, user_id: int, ver: str, limit: int, offset: int) -> str:
        '''拼数据 key：版本号编进 key 里，版本一变旧 key 自然作废'''
        return f"orders:list:{user_id}:v{ver}:{limit}:{offset}"

    async def get(self, user_id: int, limit: int, offset: int) -> GetOrdersResult | None:
        '''读缓存：先取版本号，再用版本号拼数据 key 查

        返回 None 的两种情况：
        1. 版本 key 不存在（该用户从没写过单，必然没缓存过）
        2. 数据 key 不存在（没缓存过 / 已过期 / 版本已更新）
        '''
        ver = await self.redis.get(self._ver_key(user_id))
        if ver is None:
            return None
        raw = await self.redis.get(self._data_key(user_id, ver, limit, offset))
        if raw is None:
            return None
        return self._deserialize(raw)

    async def save(self, user_id: int, limit: int, offset: int, result: GetOrdersResult) -> None:
        '''存缓存：序列化成 JSON 写入，带 60 秒 TTL'''
        ver = await self.redis.get(self._ver_key(user_id))
        if ver is None:
            ver = "0"   # 该用户还没有版本号时，先存到 v0（首次下单会 INCR 成 v1 让它作废）
        raw = self._serialize(result)
        await self.redis.set(self._data_key(user_id, ver, limit, offset), raw, ex=CACHE_TTL_SECONDS)

    async def invalidate(self, user_id: int) -> None:
        '''失效：版本号 +1，旧代的所有数据 key 立刻无人引用，等 TTL 自然回收'''
        await self.redis.incr(self._ver_key(user_id))

    def _serialize(self, result: GetOrdersResult) -> str:
        '''结果对象 → JSON 字符串

        Decimal 和 datetime 不能直接 json 序列化，转换规则：
        金额 Decimal → 字符串（避免浮点精度丢失，"9.90" 不能变 9.9）
        时间 datetime → ISO 8601 字符串（"2026-11-04T15:00:00"，可无损还原）
        状态 status 是 OrderStatus(StrEnum)，str() 后取到中文值
        '''
        return json.dumps({
            "total": result.total,
            "orders": [
                {
                    "id": o.id,
                    "order_number": o.order_number,
                    "total_amount": str(o.total_amount),
                    "status": str(o.status),
                    "created_at": o.created_at.isoformat(),
                    "updated_at": o.updated_at.isoformat(),
                }
                for o in result.orders
            ],
        }, ensure_ascii=False)

    def _deserialize(self, raw: str) -> GetOrdersResult:
        '''JSON 字符串 → 结果对象（与 _serialize 互为逆操作）

        这是基础设施层的"脏活"：Handler 拿到的永远是对象，
        JSON 长什么样、怎么编码解码，业务代码一概不知。
        '''
        data = json.loads(raw)
        return GetOrdersResult(
            total=data["total"],
            orders=[
                OrderDTO(
                    id=o["id"],
                    order_number=o["order_number"],
                    total_amount=Decimal(o["total_amount"]),          # 字符串还原为精确十进制
                    status=o["status"],
                    created_at=datetime.fromisoformat(o["created_at"]),  # ISO 字符串还原为时间
                    updated_at=datetime.fromisoformat(o["updated_at"]),
                )
                for o in data["orders"]
            ],
        )
