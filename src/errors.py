"""
错误处理模块
定义项目中的自定义异常类
"""

from .utils import color


class ServiceError(Exception):
    """
    通用服务异常基类
    所有项目异常的基类

    Attributes:
        message: 错误消息
        code: 错误代码（默认420）
        details: 额外详细信息字典
        original_exception: 原始异常对象
    """

    code = 420

    def __init__(
        self,
        message: str = None,
        code: int = None,
        details: dict = None,
        original_exception: BaseException = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息（可选）
            code: 错误代码（默认使用类属性值）
            details: 额外详细信息字典（可选）
            original_exception: 原始异常对象（用于链式异常）
        """
        self.message = message
        self.code = code if code is not None else self.__class__.code
        self.details = details or {}
        self.original_exception = original_exception

        # 构建完整消息
        if message:
            full_message = message
        elif original_exception:
            full_message = str(original_exception)
        else:
            full_message = "Unknown error"

        super().__init__(full_message)

    def __str__(self):
        """返回格式化的错误消息"""
        import shutil

        width = (
            shutil.get_terminal_size().columns
            if hasattr(shutil, "get_terminal_size")
            else 80
        )
        msg = " " * width + "\r" + color.r(self.__class__.__name__)

        if self.message:
            msg += color.r(f": {self.message}")

        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            msg += color.r(f" [{details_str}]")

        return msg

    def __repr__(self):
        """返回异常的字符串表示"""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code}, "
            f"details={self.details})"
        )

    def with_details(self, **kwargs) -> "ServiceError":
        """
        创建带有额外详细信息的新异常实例

        Args:
            **kwargs: 要添加的详细信息

        Returns:
            ServiceError: 新的异常实例（包含合并的details）
        """
        new_details = {**self.details, **kwargs}
        return self.__class__(
            message=self.message,
            code=self.code,
            details=new_details,
            original_exception=self.original_exception,
        )


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


class NetworkError(ServiceError):
    """
    网络错误
    表示网络请求相关的错误
    """

    code = 503


class DataParseError(ServiceError):
    """
    数据解析错误
    表示数据格式解析失败
    """

    code = 422


class ValidationError(ServiceError):
    """
    验证错误
    表示参数或配置验证失败
    """

    code = 400
