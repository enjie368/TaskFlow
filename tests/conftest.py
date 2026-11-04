'''pytest 公共夹具（fixture）

约定：每个测试函数都跑在一个全新的 SQLite 内存库里，测试结束即销毁。
好处：测试之间互不污染，也不会动到 MySQL 里的真实数据。

"夹具"= fixture，可以理解成"测试开始前帮你准备好的环境/数据"。
测试函数的参数名只要和夹具名对上，pytest 就会自动把它塞进来，
所以测试函数里永远看不到"创建 client""建数据库"这类代码。
'''
import httpx
import pytest_asyncio
from tortoise import Tortoise

from main import app

# 测试专用配置：连接换成内存库，模型列表和线上保持一致
# 注意：只换连接串，不换模型 —— 这样测试跑的表结构和线上完全同源
TEST_DB_CONFIG = {
    "connections": {"default": "sqlite://:memory:"},
    "apps": {
        "models": {
            "models": ["app.infrastructure.database.orm_models"],
            "default_connection": "default",
        }
    },
}


@pytest_asyncio.fixture(autouse=True)
async def init_db():
    '''每个测试前后自动建库、拆库（autouse=True 表示无需在测试里声明）。

    为什么不靠应用启动时的初始化？因为测试用的是 httpx.ASGITransport，
    它只走 ASGI 请求链路，**不执行 FastAPI 的 lifespan（启动/关闭钩子）**，
    数据库就没人初始化。所以这里手动 Tortoise.init + generate_schemas。
    generate_schemas 是按模型直接建表，相当于"跳过 aerich 迁移，一步到位"。

    yield 之前是"准备工作"，yield 之后是"收尾工作"；
    收尾里 close_connections 很关键——不关的话内存库会残留，下一条测试就脏了。
    '''
    await Tortoise.init(config=TEST_DB_CONFIG)
    await Tortoise.generate_schemas()      # 按模型建表（测试里不走 aerich）
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client():
    '''假客户端：把请求直接交给 ASGI 应用，不走网络、不起 uvicorn。

    httpx.AsyncClient 平时是发真 HTTP 的；换上 ASGITransport 后，
    请求会被直接投递给 app 对象，速度快、不用占端口，也方便调试。
    base_url 随便写（"http://test"），因为根本没有真实域名参与解析。

    async with 保证每个测试用完都关掉连接，避免资源泄漏。
    '''
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _login_headers(client, username: str, password: str = "pass1234") -> dict:
    '''内部工具函数：注册 + 登录，返回可直接用于请求的认证头。

    注意它不是夹具（没有 @fixture 装饰器），名字前面的下划线表示"仅本文件内部使用"。
    之所以要"先注册"：内存库每个测试都是空的，不注册就没有这个用户。
    注册接口若因用户名已存在而失败，这里不管——因为一旦存在，
    说明这个测试里已经建过了，登录照样能成功。

    返回形如 {"Authorization": "Bearer eyJhbGciOi..."}，
    后面所有需要"登录态"的请求都直接 headers=这个字典。
    '''
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def auth_headers(client):
    '''"默认主角"的认证头：固定是 alice 这个用户。

    绝大多数测试只需要一个能登录的人，用它就够了，测试函数里直接
    async def test_xxx(client, auth_headers) 即可拿到登录态。
    alice/bob/carol 只是密码学里的惯例占位名（甲方/乙方/第三方），不是真实账号。

    依赖 client 夹具：登录本身也要发请求，所以这里是夹具套夹具。
    '''
    return await _login_headers(client, "alice")


@pytest_asyncio.fixture
async def login_headers(client):
    '''工厂夹具：想要哪个用户，就调一次拿它的认证头。

    和 auth_headers 的区别：
      auth_headers  → 直接给你 alice 的头（一个字典）
      login_headers → 给你一个**函数**，headers = await login_headers("bob") 才拿到头
    需要"多用户对比"的测试（例如越权隔离、空列表）必须用它，
    因为要在一个测试里同时扮演 alice 和 bob。

    它同样是夹具套夹具：内部 _make 复用了 client 和 _login_headers。
    '''
    async def _make(username: str, password: str = "pass1234") -> dict:
        return await _login_headers(client, username, password)

    return _make

class FakeLoginAttemptGuard:
    '''内存版登录守卫：用字典/set 模拟 Redis 的计数与锁。

    为什么测试不用真 Redis？
    1. 测试要"随时可跑"——不依赖 Docker 容器活着；
    2. 限流的业务规则（错5次锁10分钟）和 Redis 无关，测规则就够了；
    3. 这正是 dependency_overrides 的用武之地：生产给 Redis 版，测试给内存版，
       Handler 一行不改——昨天"为什么不直接 new 实现"的答案在这里兑现。
    '''
    def __init__(self):
        self.fails: dict = {}      # 用户名 -> 连续失败次数
        self.locks: set = set()    # 被锁的用户名集合

    async def ensure_allowed(self, username):
        from app.application.common.exception import RateLimitError
        if username in self.locks:
            raise RateLimitError()

    async def record_failure(self, username):
        self.fails[username] = self.fails.get(username, 0) + 1
        if self.fails[username] >= 5:
            self.locks.add(username)

    async def reset(self, username):
        self.fails.pop(username, None)
        self.locks.discard(username)


@pytest_asyncio.fixture(autouse=True)
def override_guard():
    '''每个测试自动把真守卫换成全新的假守卫（函数级隔离，互不污染）'''
    from app.interface.dependency import get_login_attempt_guard
    fake = FakeLoginAttemptGuard()
    app.dependency_overrides[get_login_attempt_guard] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_login_attempt_guard, None)

