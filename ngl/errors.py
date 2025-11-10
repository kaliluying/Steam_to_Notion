"""
错误处理模块
定义项目中的自定义异常类
"""
from .utils import color


class ServiceError(Exception):
    """
    通用服务异常基类
    所有项目异常的基类
    """
    code = 420

    def __init__(self, msg=None, error=None, code=420):
        """
        初始化异常
        
        Args:
            msg: 错误消息（可选）
            error: 原始异常对象（可选）
            code: 错误代码（默认420）
        """
        self.code = code
        self.msg = getattr(error, "msg", str(error)) if msg is None and error else msg
        self.error = self.__class__.__name__ if error is None else error.__class__.__name__
        super().__init__(self.msg)

    def __str__(self):
        """返回格式化的错误消息"""
        msg = " "*100 + "\r" + color.r(self.error)

        if self.msg:
            msg += color.r(f": {self.msg}")

        return msg

    def __repr__(self):
        """返回异常的字符串表示"""
        return self.__str__()


class ApiError(ServiceError):
    """
    API错误基类
    所有API相关异常的基类
    """
    code = 422


class SteamApiError(ApiError):
    """
    Steam API错误
    表示Steam API相关的错误
    """
    code = 501


class SteamStoreApiError(SteamApiError):
    """
    Steam商店API错误
    表示Steam商店API请求失败
    """
    code = 481


class SteamApiNotFoundError(SteamApiError):
    """
    Steam API未找到错误
    表示请求的资源在Steam API中不存在
    """
    code = 404


class NotionApiError(ApiError):
    """
    Notion API错误
    表示Notion API相关的错误
    """
    code = 502
