'''fastapi应用入口'''
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI,Request
from tortoise import Tortoise
from fastapi.responses import JSONResponse

from app.application.common.exception import NotFoundError, ConflictError, DomainException
from app.interface.api.v1.order_router import router as order_router
from app.interface.api.v1.auth_router import router as auth_router
from config.settings import settings
from config.tortoise_config import TORTOISE_ORM

@asynccontextmanager
async def lifespan(app: FastAPI):
    '''生命周期管理器'''
    await init_database()
    yield
    await close_database()

async def init_database():
    '''初始化数据库连接（建表由 aerich 迁移管理，不再 generate_schemas）'''
    await Tortoise.init(config=TORTOISE_ORM)

async def close_database():
    '''关闭数据库连接'''
    await Tortoise.close_connections()

def _install_exception_handlers(app: FastAPI) -> None:
    '''集中翻译：业务异常 → HTTP 状态码（接口层唯一的翻译点）'''
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(DomainException)
    async def domain_handler(request: Request, exc: DomainException):
        return JSONResponse(status_code=400, content={"detail": exc.message})


def create_app()->FastAPI:
    '''创建fastapi实例'''
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="一个基于fastapi的DDD分层示例应用（JWT认证 + MySQL + aerich迁移）",
        lifespan=lifespan
    )
    _install_exception_handlers(app)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(order_router, prefix="/api/v1")
    return app
app=create_app()

@app.get("/")
async def root():
    '''根路由'''
    return {"message": "欢迎使用fastapi ddd应用","version": settings.app_version,"docs":"/docs"}


def _run_dev_server():
    '''开发模式启动（只在直接运行 main.py 时走这里）

    为什么这里不用 uvicorn 的 reload=True —— 这是"关闭 PyCharm 卡在
    「正在等待进程分离」"的根因：

      uvicorn 的 reload 是"reloader 主进程 + worker 子进程"两段式。
      Windows 没有 fork，只能走 multiprocessing spawn：worker 启动时会把
      __main__ 模块整个再跑一遍，于是又执行到 uvicorn.run(reload=True)，
      又派生一层 reloader……进程层层套娃，父子互相等对方退出。
      PyCharm 点停止/关窗口时要对整个进程树做"分离"，树上每一层都在等
      下一层，就永久卡在"正在等待进程分离"。

    正确做法：传 app **对象**而不是 "main:app" 字符串，并关掉 reload。
    传对象时 uvicorn 不会重新 import 模块，__main__ 块只执行一次，
    进程树只有一层，停止时直接退出。
    '''
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    _run_dev_server()
