"""
常量与枚举定义

包含在线状态、隐私等级以及 API 文档模板。
"""

__author__ = "SmileyBarry"


class Enum(object):
    """
    枚举基类。

    禁止实例化，只能使用其属性。
    """

    def __init__(self):
        raise TypeError("Enums cannot be instantiated, use their attributes instead")


class CommunityVisibilityState(Enum):
    """
    个人资料可见性枚举。

    定义 Steam 用户个人资料的隐私级别。
    """

    PRIVATE = 1  # 私密
    FRIENDS_ONLY = 2  # 仅好友可见
    FRIENDS_OF_FRIENDS = 3  # 好友的好友可见
    USERS_ONLY = 4  # 仅用户可见
    PUBLIC = 5  # 公开


class OnlineState(Enum):
    """
    在线状态枚举。

    定义 Steam 用户的在线状态。
    """

    OFFLINE = 0  # 离线
    ONLINE = 1  # 在线
    BUSY = 2  # 忙碌
    AWAY = 3  # 离开
    SNOOZE = 4  # 休眠
    LOOKING_TO_TRADE = 5  # 想要交易
    LOOKING_TO_PLAY = 6  # 想要游戏


import builtins

# 检测是否在 IPython 环境中运行
_get_ipython = getattr(builtins, "get_ipython", None)
_in_ipython = callable(_get_ipython) and _get_ipython()

# 如果在 IPython 中，定义所有 IPython 的自定义函数/方法名称，
# 以便我们可以对它们进行特殊处理。
ipython_peeves = ["trait_names", "getdoc"] if _in_ipython else []
ipython_mode = bool(_in_ipython)

# API 调用文档字符串模板（不缩进，以免文档字符串过度缩进）
API_CALL_DOCSTRING_TEMPLATE = """
{name}

Parameters:
{parameter_list}
"""
# API 调用参数模板
API_CALL_PARAMETER_TEMPLATE = (
    "{indent}{{requirement}} {{type}} {{name}}:{indent}{{desc}}"
)
