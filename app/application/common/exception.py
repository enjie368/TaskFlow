'''
通用业务异常
'''

from typing import Optional



class DomainException(Exception):
    '''业务异常'''
    def __init__(self, message:str,code:Optional[str]=None) -> None:
        self.message = message
        self.code = code
        super().__init__(message)

class AuthError(DomainException):
    '''认证异常'''
    def __init__(self,message="认证失败"):
        super().__init__(message,"AuthError")

class DuplicateError(DomainException):
    '''重复数据异常'''
    def __init__(self,message="数据已经存在"):
        super().__init__(message,"DuplicateError")

class NotFoundError(DomainException):
    '''数据不存在异常'''
    def __init__(self,message="数据不存在"):
        super().__init__(message,"NotFoundError")

class ValidationError(DomainException):
    '''数据验证异常'''
    def __init__(self,message="数据验证失败"):
        super().__init__(message,"ValidationError")