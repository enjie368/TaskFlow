'''
Tortoise ORM 统一配置
- main.py 启动时用它初始化数据库连接
- aerich 迁移工具也读这份（aerich 不认识 main.py）
- 以后增删 ORM 模型，只需要改这里的 models 列表
'''
from config.settings import settings

TORTOISE_ORM = {
    "connections": {
        "default": settings.db_url,   # 来自 .env 的 DB_URL，当前指向 MySQL taskflow 库
    },
    "apps": {
        "models": {
            "models": [
                "aerich.models",                              # aerich 自己的版本记录表
                "app.infrastruture.database.orm_models",      # 业务 ORM 模型
            ],
            "default_connection": "default",
        },
    },
}
