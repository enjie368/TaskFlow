'''fastapi应用入口'''
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from tortoise import Tortoise
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

def create_app()->FastAPI:
    '''创建fastapi实例'''
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="一个基于fastapi的DDD分层示例应用（JWT认证 + MySQL + aerich迁移）",
        lifespan=lifespan
    )
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(order_router, prefix="/api/v1")
    return app
app=create_app()

@app.get("/")
async def root():
    '''根路由'''
    return {"message": "欢迎使用fastapi ddd应用","version": settings.app_version,"docs":"/docs"}

if __name__=="__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000,reload=settings.debug)