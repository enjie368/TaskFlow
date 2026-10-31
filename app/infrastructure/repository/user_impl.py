from typing import Optional
from app.domain.shared.vo import UserID
from app.domain.user.entity import User
from app.domain.user.repository import UserRepository
from app.infrastructure.database.mappers import UserMapper
from app.infrastructure.database.orm_models import UserORM


class UserRepositoryImpl(UserRepository):

    async def save(self, user: User)->User:
        '''保存用户'''
        user_orm=UserMapper.to_orm(user)
        await user_orm.save()
        return UserMapper.to_entity(user_orm)

    async def find_by_id(self, user_id: UserID) -> Optional[User]:
        '''通过id查找用户'''
        orm_model = await UserORM.get_or_none(id=user_id.value)
        if orm_model:
            return UserMapper.to_entity(orm_model)
        return None

    async def find_by_name(self, name: str) -> Optional[User]:
        '''通过姓名查找用户'''
        orm_model = await UserORM.get_or_none(username=name)
        if orm_model :
            return UserMapper.to_entity(orm_model)
        return None

    async def exist_by_name(self, name: str) -> bool:
        '''检查用户是否存在'''
        return await UserORM.exists(username=name)

    async def delete(self, user_id: UserID)->bool:
        '''删除用户'''
        count=await UserORM.filter(id=user_id.value).delete()
        return count>0

    async def search_all(self) -> list[User]:
        '''查找所有用户'''
        orm_models=await UserORM.all()
        return [UserMapper.to_entity(orm_model) for orm_model in orm_models]