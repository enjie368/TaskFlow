from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        '''把明文密码加秘密'''
        pass

    @abstractmethod
    def verify(self, password: str, hashed_password: str) -> bool:
        '''检验明文与密码是否匹配'''
        pass