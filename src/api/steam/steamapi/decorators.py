"""
通用装饰器与缓存工具

包含 TTL 缓存属性与单例实现。
"""

__author__ = "SmileyBarry"

import threading
import time


class debug(object):
    @staticmethod
    def no_return(originalFunction, *args, **kwargs):
        """断言函数不应返回（调试用）。"""

        def callNoReturn(*args, **kwargs):
            originalFunction(*args, **kwargs)
            # 这段代码永远不应该返回！
            raise AssertionError("No-return function returned.")

        return callNoReturn


MINUTE = 60
HOUR = 60 * MINUTE
INFINITE = 0


class cached_property(object):
    """(C) 2011 Christopher Arndt, MIT License

    仅在 TTL 期内评估一次的只读属性装饰器。

    它可以用于创建这样的缓存属性::

        import random

        # 包含属性的类必须是一个新式类
        class MyClass(object):
            # 创建一个值缓存十分钟的属性
            @cached_property(ttl=600)
            def randint(self):
                # 最多每 10 分钟评估一次。
                return random.randint(0, 100)

    该值缓存在具有由此装饰器包装的属性 getter 方法的对象实例的 '_cache' 属性中。
    '_cache' 属性值是一个字典，其中包含对象的每个由此装饰器包装的属性的键。
    缓存中的每个条目仅在首次访问属性时创建，并且是一个包含最后计算的属性值
    和自纪元以来最后更新时间的两元素元组（以秒为单位）。

    默认的生存时间（TTL）为 300 秒（5 分钟）。将 TTL 设置为零以使缓存的值永不过期。

    要手动使缓存的属性值过期，只需执行::

        del instance._cache[<property name>]

    """

    def __init__(self, ttl=300):
        # ttl=0 表示永不过期
        self.ttl = ttl

    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        now = time.time()
        value, last_update = None, None
        if not hasattr(inst, "_cache"):
            inst._cache = {}

        entry = inst._cache.get(self.__name__, None)
        if entry is not None:
            value, last_update = entry
            if now - last_update > self.ttl > 0:
                entry = None

        if entry is None:
            value = self.fget(inst)
            cache = inst._cache
            cache[self.__name__] = (value, now)

        return value


class Singleton:
    """
    线程安全单例装饰器。

    一个非线程安全的辅助类，用于简化实现单例。
    这应该用作装饰器——而不是元类——应用于
    应该是单例的类。

    装饰后的类可以定义一个 `__init__` 函数，该函数
    仅接受 `self` 参数。除此之外，对装饰后的类
    没有任何限制。

    限制：装饰后的类不能被继承。

    :author: Paul Manta, Stack Overflow.
             http://stackoverflow.com/a/7346105/2081507
             （稍作修改）

    """

    def __init__(self, decorated):
        self._lock = threading.Lock()
        self._decorated = decorated

    def __call__(self, *args, **kwargs):
        """
        返回单例实例。首次调用时，它创建一个
        装饰后的类的新实例并调用其 `__init__` 方法。
        在所有后续调用中，返回已创建的实例。

        """
        with self._lock:
            try:
                return self._instance
            except AttributeError:
                self._instance = self._decorated(*args, **kwargs)
                return self._instance

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
