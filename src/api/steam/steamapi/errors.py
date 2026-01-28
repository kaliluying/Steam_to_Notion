"""
Steam API 异常体系与响应错误映射

通过 HTTP 状态码转为更语义化的异常类型。
"""

__author__ = "SmileyBarry"

from .decorators import debug


class APIException(Exception):
    """
    API 异常基类。

    Base class for all API exceptions.
    """

    pass


class AccessException(APIException):
    """
    权限不足或访问被拒绝（如私密用户）。

    您正在尝试查询您没有权限查询的对象。（例如：私密用户、
    隐藏的截图等）
    """

    pass


class APIUserError(APIException):
    """
    由用户输入导致的错误（如参数错误或空结果）。

    由用户错误引起的 API 错误，例如错误的数据或查询的空结果。
    """

    pass


class UserNotFoundError(APIUserError):
    """
    用户未找到（无效的 vanity URL 或 SteamID）。

    在 Steam 社区上找不到指定的用户。（错误的个性化 URL？不存在的 ID？）
    """

    pass


class APIError(APIException):
    """
    API 服务端错误或临时异常。

    API 错误表示服务器有问题、临时问题或其他容易修复的问题。
    """

    pass


class APIFailure(APIException):
    """
    请求失败（参数、配置或权限问题）。

    API 失败表示您的请求有问题（例如：无效的 API）、数据有问题，
    或因不当使用导致的任何错误。
    """

    pass


class APIBadCall(APIFailure):
    """
    调用参数与接口规范不匹配。

    您的 API 调用与 API 的规范不匹配。请检查您的参数、服务名称、命令和版本。
    """

    pass


class APINotFound(APIFailure):
    """
    接口或服务不存在（404）。

    您尝试调用的 API 不存在。（404）
    """

    pass


class APIUnauthorized(APIFailure):
    """
    未授权或权限不足（401）。

    您尝试调用的 API 需要密钥，或者您的密钥权限不足。
    如果您正在请求用户详细信息，请确保其隐私级别允许您这样做，
    或者您已正确授权该用户。（401）
    """

    pass


class APIKeyRequired(APIFailure):
    """
    该接口必须提供 API Key。

    此 API 需要 API 密钥才能调用，并且不支持匿名请求。
    """

    pass


class APIPrivate(APIFailure):
    """
    需要更高权限的 API Key。

    您尝试调用的 API 需要特权 API 密钥。您现有的密钥不允许调用此 API。
    """


class APIConfigurationError(APIFailure):
    """
    配置错误（APIConnection/APIInterface 参数不正确）。

    没有定义 APIConnection，或者给 "APIConnection" 或 "APIInterface" 的参数无效。
    """

    pass


def check(response):
    """
    根据 HTTP 状态码抛出对应异常。

    :type response: requests.Response
    """
    if response.status_code // 100 == 4:
        if response.status_code == 404:
            raise APINotFound(
                "The function or service you tried to call does not exist."
            )
        elif response.status_code == 401:
            raise APIUnauthorized("This API is not accessible to you.")
        elif response.status_code == 403:
            if "?key=" in response.request.url or "&key=" in response.request.url:
                raise APIPrivate(
                    "You have no permission to use this API, or your key may be invalid."
                )
            else:
                raise APIKeyRequired("This API requires a key to call.")
        elif response.status_code == 400:
            raise APIBadCall(
                "The parameters you sent didn't match this API's requirements."
            )
        else:
            raise APIFailure(
                "Something is wrong with your configuration, parameters or environment."
            )
    elif response.status_code // 100 == 5:
        raise APIError("The API server has encountered an unknown error.")
    else:
        return
