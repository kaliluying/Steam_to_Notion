"""
工具函数模块
提供颜色输出、文件操作、重试装饰器等实用功能
"""

import json
import os
import sys
import time
from functools import wraps

from termcolor import colored

# Windows平台需要初始化colorama以支持颜色输出
if sys.platform == "win32":
    import colorama

    os.system("color")
    colorama.init()


class ColorText:
    """
    颜色文本工具类
    提供返回不同颜色文本的静态方法
    """

    @staticmethod
    def r(msg):
        """返回红色文本"""
        return colored(msg, "red")

    @staticmethod
    def g(msg):
        """返回绿色文本"""
        return colored(msg, "green")

    @staticmethod
    def y(msg):
        """返回黄色文本"""
        return colored(msg, "yellow")

    @staticmethod
    def c(msg):
        """返回青色文本"""
        return colored(msg, "cyan")

    @staticmethod
    def m(msg):
        """返回洋红色文本"""
        return colored(msg, "magenta")


class Echo:
    """
    彩色输出工具类
    提供打印不同颜色消息的静态方法
    """

    @staticmethod
    def _colored(msg, color):
        """将消息着色"""
        return colored(msg, color)

    @staticmethod
    def _color_print(msg, color, **kwargs):
        """打印彩色消息并刷新输出缓冲区"""
        print(Echo._colored(msg, color=color), **kwargs)
        sys.stdout.flush()

    @staticmethod
    def r(msg, **kwargs):
        """打印红色消息"""
        Echo._color_print(msg, "red", **kwargs)

    @staticmethod
    def g(msg, **kwargs):
        """打印绿色消息"""
        Echo._color_print(msg, "green", **kwargs)

    @staticmethod
    def y(msg, **kwargs):
        """打印黄色消息"""
        Echo._color_print(msg, "yellow", **kwargs)

    @staticmethod
    def c(msg, **kwargs):
        """打印青色消息"""
        Echo._color_print(msg, "cyan", **kwargs)

    @staticmethod
    def m(msg, **kwargs):
        """打印洋红色消息"""
        Echo._color_print(msg, "magenta", **kwargs)

    def __call__(self, *args, **kwargs):
        """直接调用时打印消息并刷新输出缓冲区"""
        print(*args, **kwargs)
        sys.stdout.flush()


# 全局实例
echo = Echo()  # 用于打印彩色消息
color = ColorText()  # 用于返回彩色文本


def soft_exit(exit_code):
    """
    软退出函数
    在Windows平台上会等待用户按键后再退出

    Args:
        exit_code: 退出代码
    """
    if sys.platform == "win32":
        input(color.y("\n按任意键退出"))
    sys.exit(exit_code)


def load_from_file(filename):
    """
    从JSON文件加载数据

    Args:
        filename: 文件名

    Returns:
        dict: 从文件加载的字典，如果文件不存在则返回空字典
    """
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as f:
        return json.load(f)


def dump_to_file(d, filename):
    """
    将数据保存到JSON文件

    Args:
        d: 要保存的字典
        filename: 文件名
    """
    with open(filename, "w") as f:
        json.dump(d, f)


def retry(
    exceptions,
    on_code=None,
    retry_num=3,
    initial_wait=0.5,
    backoff=2,
    raise_on_error=True,
    debug_msg=None,
    debug=False,
):
    """
    重试装饰器
    当函数抛出指定异常时自动重试

    Args:
        exceptions: 要捕获的异常类型（可以是元组）
        on_code: 仅在特定错误代码时重试（可选）
        retry_num: 重试次数
        initial_wait: 初始等待时间（秒）
        backoff: 退避倍数（每次重试等待时间乘以该值）
        raise_on_error: 重试失败后是否抛出异常
        debug_msg: 调试消息（可选）
        debug: 是否显示调试信息

    Returns:
        装饰器函数
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            _tries, _delay = retry_num + 1, initial_wait
            while _tries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    # 如果指定了错误代码且不匹配，则直接抛出或返回None
                    if on_code is not None and on_code != e.code:
                        if raise_on_error:
                            raise
                        return None
                    _tries -= 1
                    # 如果重试次数用完
                    if _tries == 1:
                        if raise_on_error:
                            raise
                        return None
                    # 计算下次等待时间
                    _delay *= backoff
                    if debug:
                        # 显示调试信息
                        print_args = args if args else ""
                        msg = (
                            str(
                                f"函数: {f.__name__} 参数: {print_args}, kwargs: {kwargs}\n"
                                f"异常: {e}\n"
                            )
                            if debug_msg is None
                            else color.m(debug_msg)
                        )
                        echo.m("\n" + msg)
                        # 倒计时显示
                        for s in range(_delay, 1, -1):
                            echo.m(" " * 20 + f"\r等待 {s} 秒...", end="\r")
                            time.sleep(1)
                    else:
                        time.sleep(_delay)

        return wrapper

    return decorator
