# TaskFlow

基于 **FastAPI + DDD 分层架构** 的订单服务示例，包含 JWT 认证、MySQL 持久化与 Aerich 数据库迁移。

项目按领域驱动设计（DDD）拆成四层，领域层不依赖任何 Web 框架或 ORM，便于替换基础设施和编写单元测试。

## 技术栈

| 分类 | 选型 |
| --- | --- |
| 语言 / 运行时 | Python 3.13 |
| Web 框架 | FastAPI 0.143 + Uvicorn |
| ORM | Tortoise ORM 0.25（全异步） |
| 数据库 | MySQL 9（utf8mb4） |
| 迁移工具 | Aerich 0.9 |
| 认证 | PyJWT（HS256）+ bcrypt |
| 配置管理 | pydantic-settings + `.env` |

## 功能

- 用户注册 / 登录，密码经 bcrypt 加盐哈希后存储，明文不落库
- 登录签发 JWT（HS256，默认 60 分钟过期），`GET /auth/me` 校验并返回当前身份
- 订单分页查询，`WHERE user_id = ?` 保证只能看到自己的数据
- 创建订单：订单号由领域层生成，金额精度对齐数据库 `DECIMAL(10,2)`，初始状态由业务规则决定

## 架构

```mermaid
flowchart LR
    A[interface<br/>路由 + 依赖注入] --> B[application<br/>用例编排]
    B --> C[domain<br/>实体 / 值对象 / 仓储接口]
    D[infrastructure<br/>Tortoise / bcrypt / JWT] -.实现.-> C
    A --> D
```

一次「创建订单」请求的流向：

```
POST /api/v1/orders/
  └─ order_router.create_order()          解析请求体、从 token 取 user_id
      └─ CreateOrderHandler.handle()       应用层：校验参数、编排
          ├─ Order.create()                领域层：生成订单号 / 状态 / 金额精度
          └─ OrderRepository.add()         仓储接口（domain 定义）
              └─ OrderRepositoryImpl       基础设施层：OrderORM.save()
```

关键约束：**依赖方向永远指向内层**。`domain` 里不会出现 `tortoise`、`fastapi` 的任何 import。

## 目录结构

```
TaskFlow/
├── app/
│   ├── domain/                  # 领域层：纯 Python，无框架依赖
│   │   ├── shared/vo.py         # UserID 值对象（frozen dataclass）
│   │   ├── user/                # User 实体、PasswordHasher 抽象、UserRepository 接口
│   │   └── order/               # Order 实体（含订单号生成规则）、OrderRepository 接口
│   ├── application/             # 应用层：用例编排
│   │   ├── common/              # DomainException 体系、TokenService 抽象
│   │   ├── user/commands/       # 注册、登录
│   │   ├── user/queries/        # 订单查询
│   │   └── order/commands/      # 创建订单
│   ├── infrastructure/          # 基础设施层：外部依赖的具体实现
│   │   ├── database/            # orm_models（表定义）、mappers（实体 ↔ ORM 转换）
│   │   ├── repository/          # user_impl、order_impl
│   │   └── security/            # bcrypt_hasher、jwt_service
│   └── interface/               # 接口层
│       ├── api/v1/              # auth_router、order_router
│       ├── dependency.py        # FastAPI 依赖注入装配
│       └── security.py          # get_current_user_id：解析 Bearer token
├── config/
│   ├── settings.py              # Pydantic Settings，读取 .env
│   └── tortoise_config.py       # TORTOISE_ORM，main.py 与 aerich 共用
├── migrations/                  # Aerich 生成的迁移脚本（数据库版本控制）
├── main.py                      # 应用入口
├── pyproject.toml               # Aerich 配置
└── requirements.txt
```

## 快速开始

```bash
# 1. 建库
mysql -uroot -p -e "CREATE DATABASE taskflow DEFAULT CHARACTER SET utf8mb4;"

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy .env.example .env          # mac/linux 用 cp
# 编辑 .env，填入 JWT_SECRET 与 DB_URL

# 4. 执行数据库迁移
aerich upgrade

# 5. 启动
python main.py
```

打开 http://127.0.0.1:8000/docs 查看交互式接口文档。

`.env` 示例：

```ini
JWT_SECRET=<用 python -c "import secrets;print(secrets.token_urlsafe(48))" 生成>
DB_URL=mysql://root:your_password@localhost:3306/taskflow
```

## 接口一览

| 方法 | 路径 | 说明 | 需要认证 |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register` | 注册用户 | 否 |
| POST | `/api/v1/auth/login` | 登录，返回 access_token | 否 |
| GET | `/api/v1/auth/me` | 当前登录用户信息 | 是 |
| GET | `/api/v1/orders/` | 我的订单列表，支持 `limit` / `offset` | 是 |
| POST | `/api/v1/orders/` | 创建订单，body: `{"total_amount": 88.5}` | 是 |

认证方式：请求头 `Authorization: Bearer <token>`。

## 数据库迁移

表结构由 Aerich 管理，不使用 `generate_schemas()`。

```bash
aerich migrate --name add_something   # 对比模型变化，生成迁移脚本
aerich upgrade                        # 应用到数据库
aerich downgrade                      # 回滚一步
```

改动 `app/infrastructure/database/orm_models.py` 后必须走这三步，迁移脚本本身要提交到仓库——它就是数据库的版本历史。

## 设计要点

- **值对象**：`UserID` 用 `frozen dataclass` 表达，`__post_init__` 里校验非负，避免把裸 int 到处传递。
- **仓储接口放领域层**：`UserRepository` / `OrderRepository` 是抽象类，具体实现留在基础设施层，应用层只依赖抽象。
- **认证与授权分离**：token 只负责证明「你是谁」（签名校验），数据隔离靠查询条件 `WHERE user_id = ?`（证明「你能看什么」）。
- **金额用 `Decimal`**：实体、DTO、数据库字段统一 `Decimal`，避免 `0.1 + 0.2 != 0.3` 的浮点误差。
- **身份只来自 token**：下单接口的请求体里没有 `user_id`，防止改个数字就能给别人下单（越权 / IDOR）。

## Roadmap

- [ ] 登录失败次数限制（Redis 计数）
- [ ] 下单幂等（`Idempotency-Key` 去重）
- [ ] 订单状态机（待处理 → 已支付 → 已完成 / 已取消）
- [ ] pytest + httpx 接口测试
