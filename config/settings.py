'''
应用配置管理
'''
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent   # 项目根目录

class Settings(BaseSettings):
    '''
    应用配置类
    '''
    #应用配置
    app_name: str="TaskFlow"
    app_version: str="1.0.0"
    debug: bool=True
    #secret_key: str="secret"

    #redis配置
    redis_url: str = "redis://127.0.0.1:6379/0"

    #数据库配置
    db_url: str="sqlite://data/test.db"
    #jwt配置
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config =ConfigDict(
        env_file=BASE_DIR/".env",
        env_file_encoding="utf-8"
    )

settings = Settings()

if __name__ == '__main__':
    print(settings.app_name)
