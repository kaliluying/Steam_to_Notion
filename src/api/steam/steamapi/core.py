"""
Steam Web API 核心封装

提供动态 API 调用、响应对象化、缓存与接口自发现能力。
"""

__author__ = "SmileyBarry"

import typing as tp

import requests
import time

from .consts import (
    API_CALL_DOCSTRING_TEMPLATE,
    API_CALL_PARAMETER_TEMPLATE,
    ipython_peeves,
    ipython_mode,
)
from .decorators import Singleton, cached_property, INFINITE
from .errors import (
    APIException,
    APIUnauthorized,
    APIKeyRequired,
    APIPrivate,
    APIConfigurationError,
)
from . import errors

GET = "GET"
POST = "POST"

# Steam Web API 参数类型到 Python 类型的映射
# 用于参数校验和自动转换。
APITypes: tp.Dict[str, tp.Any] = {
    "bool": bool,
    "int32": int,
    "uint32": int,
    "uint64": int,
    "string": [str],
    "rawbinary": [str, bytes],
}


class APICall(object):
    def __init__(self, api_id: str, parent: tp.Any, method: tp.Optional[str] = None):
        """
        API 调用节点，支持链式访问与动态方法构建。

        创建一个新的 APICall 实例。

        :param api_id: API 的字符串标识符。必须以字母开头，符合 Python 属性命名规则。
        :type api_id: str
        :param parent: 此 APICall 对象的父级。如果是服务或接口，则提供 APIInterface 实例。
        :type parent: APICall 或 APIInterface
        :param method: 调用 API 时使用的 HTTP 方法。
        :type method: str
        :return: 一个新的 APICall 实例。
        :rtype: APICall
        """
        self._api_id = api_id
        self._is_registered = False
        self._parent = parent
        self._method = method

        # 缓存上层 API Key 与最终 URL，减少重复计算
        self._cached_key = None
        self._query = ""

        # Set an empty documentation for now.
        self._api_documentation = ""

    @property
    def _api_key(self) -> tp.Optional[str]:
        """
        获取当前调用链可用的 API Key（向上查找并缓存）。

        获取适用的 API 密钥（如果存在）。

        如果在此调用的 APIInterface "祖父级"（因为每个 APICall 都有一个 APICall 父级）中定义了密钥，
        则该密钥将被此对象无限期使用并缓存。（直到对象销毁）

        否则，将不返回任何内容（None）。

        :return: 字符串形式的 Steam Web API 密钥，如果不可用则返回 None。
        :rtype: str 或 None
        """
        if self._cached_key is not None:
            return self._cached_key

        if self._parent is not None:
            self._cached_key = self._parent._api_key
            return self._cached_key

        # No key is available. (This is OK)
        return None

    def _build_query(self) -> str:
        """构建并缓存最终请求 URL。"""
        if self._query != "":
            return self._query

        # Build the query by calling "str" on ourselves, which recursively
        # calls "str" on each parent in the chain.
        self._query = str(self)
        return self._query

    def __str__(self) -> str:
        """
        生成函数 URL（递归拼接父节点）。
        """
        if isinstance(self._parent, APIInterface):
            return "{base}{name}/".format(
                base=self._parent._query_template, name=self._api_id
            )
        else:
            return "{base}{name}/".format(base=str(self._parent), name=self._api_id)

    @cached_property(ttl=INFINITE)
    def _full_name(self):
        if self._parent is None:
            return self._api_id
        else:
            return "{parent}.{name}".format(
                parent=self._parent._full_name, name=self._api_id
            )

    def __repr__(self):
        if self._is_registered is True:
            # This is a registered, therefore working, API.
            note = "(verified)"
        else:
            note = "(unconfirmed)"
        return "<{cls} {full_name} {api_note}>".format(
            cls=self.__class__.__name__, full_name=self._full_name, api_note=note
        )

    def __getattribute__(self, item):
        if item.startswith("_"):
            # Underscore items are special.
            return super(APICall, self).__getattribute__(item)
        else:
            try:
                return super(APICall, self).__getattribute__(item)
            except AttributeError:
                if ipython_mode is True:
                    # We're in IPython. Which means "getdoc()" is also
                    # automatically used for docstrings!
                    if item == "getdoc":
                        return lambda: self._api_documentation
                    elif item in ipython_peeves:
                        # IPython always looks for this, no matter what (hiding it in __dir__ doesn't work), so this is
                        # necessary to keep it from constantly making new
                        # APICall instances. (a significant slowdown)
                        raise
                # Not an expected item, so generate a new APICall!
                return APICall(item, self)

    def __iter__(self):
        return self.__dict__.__iter__()

    def _set_documentation(self, docstring: str) -> None:
        """
        绑定当前 API 调用的文档字符串（用于交互式提示）。

        为此 APICall 实例设置特定的文档字符串，解释绑定的函数。

        :param docstring: 相关的文档字符串。
        :return: None
        """
        self._api_documentation = docstring

    def _register(self, apicall_child: tp.Optional["APICall"] = None) -> None:
        """
        将已确认可用的 APICall 注册到调用链上，避免重复创建。

        在 "self._resolved_children" 字典中注册子 APICall 对象，以便正常使用。
        由 API 函数包装器在确认工作后使用。

        :param apicall_child: 一个可用的 APICall 对象，应存储为已解析的对象。
        :type apicall_child: APICall
        """
        if apicall_child is not None:
            if (
                apicall_child._api_id in self.__dict__
                and apicall_child is not self.__dict__[apicall_child._api_id]
            ):
                raise KeyError("This API ID is already taken by another API function!")
        if not isinstance(self._parent, APIInterface):
            self._parent._register(self)
        else:
            self._is_registered = True
        if apicall_child is not None:
            self.__setattr__(apicall_child._api_id, apicall_child)
            apicall_child._is_registered = True

    def _convert_arguments(self, kwargs: tp.Dict[str, tp.Any]) -> None:
        """
        将参数转换为 Web API 接受的格式（列表拼接、布尔转 0/1）。

        将给定参数的类型转换为调用友好的格式。直接修改给定的字典。

        :param kwargs: 传递给调用函数的关键字参数字典。
        :type kwargs: dict
        :return: None，因为给定的字典会被就地修改。
        :rtype: None
        """
        for argument in kwargs:
            if issubclass(type(kwargs[argument]), list):
                # The API takes multiple values in a "a,b,c" structure, so we
                # have to encode it in that way.
                kwargs[argument] = ",".join(kwargs[argument])
            elif issubclass(type(kwargs[argument]), bool):
                # The API treats True/False as 1/0. Convert it.
                if kwargs[argument] is True:
                    kwargs[argument] = 1
                else:
                    kwargs[argument] = 0

    def __call__(self, method: str = GET, **kwargs: tp.Any):
        """执行 API 调用并返回 APIResponse 或原始内容。"""
        self._convert_arguments(kwargs)

        automatic_parsing = True
        if "format" in kwargs:
            automatic_parsing = False
        else:
            kwargs["format"] = "json"

        if self._api_key is not None:
            kwargs["key"] = self._api_key

        # Format the final query.
        query = str(self)

        if self._method is not None:
            method = self._method

        if method == POST:
            response = requests.request(method, query, data=kwargs)
        else:
            response = requests.request(method, query, params=kwargs)

        errors.check(response)

        # Store the object for future reference.
        if self._is_registered is False:
            self._parent._register(self)

        if automatic_parsing is True:
            response_obj = response.json()
            if len(response_obj.keys()) == 1 and "response" in response_obj:
                return APIResponse(response_obj["response"])
            else:
                return APIResponse(response_obj)
        else:
            if kwargs["format"] == "json":
                return response.json()
            else:
                return response.content


class APIInterface(object):
    def __init__(
        self,
        api_key: tp.Optional[str] = None,
        autopopulate: bool = False,
        strict: bool = False,
        api_domain: str = "api.steampowered.com",
        api_protocol: str = "https",
        settings: tp.Optional[tp.Dict[str, tp.Any]] = None,
        validate_key: bool = False,
    ):
        """
        API 接口入口：支持自动发现接口与严格模式调用。

        初始化一个新的 APIInterface 对象。此对象定义了一个 API 交互会话，用于从标准代码调用任何 API 函数。

        :param api_key: 您的 Steam Web API 密钥。可以留空，但某些 API 将无法工作。
        :type api_key: str
        :param autopopulate: 是否应在初始化期间自动填充 Steam Web API 支持的接口、服务和方法。
        :type autopopulate: bool
        :param strict: 接口是否应强制仅访问已定义的函数，并且仅按定义访问。仅当 :var autopopulate: 为 True 时适用。
        :type strict: bool
        :param api_domain: API 域名。
        :param settings: 定义高级设置的字典。
        :type settings: dict
        :param validate_key: 使用给定密钥对 API 执行测试调用，以确保密钥有效且正常工作。
        :return:
        """
        if autopopulate is False and strict is True:
            raise ValueError(
                '"strict" is only applicable if "autopopulate" is set to True.'
            )

        if api_protocol not in ("http", "https"):
            raise ValueError('"api_protocol" must either be "http" or "https".')

        if "/" in api_domain:
            raise ValueError(
                '"api_domain" should only contain the domain name itself, without any paths or queries.'
            )

        if isinstance(api_key, str) and len(api_key) == 0:
            # We were given an empty key (== no key), but the API's equivalent
            # of "no key" is None.
            api_key = None

        if settings is None:
            # Working around mutable argument defaults.
            settings = dict()

        super_self = super(type(self), self)

        # Initialization routines must use the original __setattr__ function, because they might collide with the
        # overridden "__setattr__", which expects a fully-built instance to
        # exist before being called.
        def set_attribute(name, value):
            return super_self.__setattr__(name, value)

        set_attribute("_api_key", api_key)
        set_attribute("_strict", strict)
        set_attribute("_settings", settings)

        query_template = "{proto}://{domain}/".format(
            proto=api_protocol, domain=api_domain
        )
        set_attribute("_query_template", query_template)

        if autopopulate is True:
            # TODO: Autopopulation should be long-term-cached somewhere for
            # future use, since it won't change much.

            # Regardless of "strict mode", it has to be OFF during
            # auto-population.
            original_strict_value = self._strict
            try:
                self.__dict__["_strict"] = False
                self._autopopulate_interfaces()
            finally:
                self.__dict__["_strict"] = original_strict_value
        elif validate_key is True:
            if api_key is None:
                raise ValueError('"validate_key" is True, but no key was given.')

            # Call "GetSupportedAPIList", which is guaranteed to succeed with
            # any valid key. (Or no key)
            try:
                api_util = tp.cast(tp.Any, self).ISteamWebAPIUtil
                get_supported = getattr(api_util.GetSupportedAPIList, "v1")
                get_supported(key=self._api_key)
            except (APIUnauthorized, APIKeyRequired, APIPrivate):
                raise APIConfigurationError("This API key is invalid.")

    def _autopopulate_interfaces(self) -> None:
        """根据 GetSupportedAPIList 自动生成接口、方法与文档。"""
        # Call the API which returns a list of API Services and Interfaces.
        # API definitions describe how the Interfaces and Services are built
        # up, including parameter names & types.
        api_util = tp.cast(tp.Any, self).ISteamWebAPIUtil
        get_supported = getattr(api_util.GetSupportedAPIList, "v1")
        api_definition = get_supported(key=self._api_key)
        api_definition = tp.cast(tp.Any, api_definition)

        for interface in api_definition.apilist.interfaces:
            interface_object = APICall(interface.name, self)
            parameter_description = API_CALL_PARAMETER_TEMPLATE.format(indent="\t")

            for method in interface.methods:
                if method.name in interface_object:
                    base_method_object = interface_object.__getattribute__(method.name)
                else:
                    base_method_object = APICall(
                        method.name, interface_object, method.httpmethod
                    )
                # API calls have version-specific definitions, so backwards compatibility could be maintained.
                # However, the Web API returns versions as integers (1, 2,
                # etc.) but accepts them as "v?" (v1, v2, etc.)
                method_object = APICall(
                    "v" + str(method.version), base_method_object, method.httpmethod
                )

                parameters = []
                for parameter in method.parameters:
                    parameter_requirement = "REQUIRED"
                    if parameter.optional is True:
                        parameter_requirement = "OPTIONAL"
                    if "description" in parameter:
                        desc = parameter.description
                    else:
                        desc = "(no description)"
                    parameters += [
                        parameter_description.format(
                            requirement=parameter_requirement,
                            type=parameter.type,
                            name=parameter.name,
                            desc=desc,
                        )
                    ]
                # Now build the docstring.
                func_docstring = API_CALL_DOCSTRING_TEMPLATE.format(
                    name=method.name, parameter_list="\n".join(parameters)
                )
                # Set the docstring appropriately
                method_object._api_documentation = func_docstring

                # Now call the standard registration method.
                method_object._register()
            # And now, add it to the APIInterface.
            setattr(self, interface.name, interface_object)

    def __getattr__(self, name: str):
        """
        在非 strict 模式下，动态生成服务节点。

        如果 "strict" 被禁用，则创建一个新的 APICall() 实例。

        :param name: 服务或接口名称。
        :return: 用于访问远程服务或接口的 Python 对象。（APICall）
        :rtype: APICall
        """
        if name.startswith("_"):
            return super(type(self), self).__getattribute__(name)
        elif name in ipython_peeves:
            # IPython always looks for this, no matter what (hiding it in __dir__ doesn't work), so this is
            # necessary to keep it from constantly making new APICall
            # instances. (a significant slowdown)
            raise AttributeError()
        else:
            if self._strict is True:
                raise AttributeError(
                    "Strict '{cls}' object has no attribute '{attr}'".format(
                        cls=type(self).__name__, attr=name
                    )
                )
            new_service = APICall(name, self)
            # Save this service.
            self.__dict__[name] = new_service
            return new_service

    def __setattr__(self, name: str, value: tp.Any):
        if self._strict is True:
            raise AttributeError(
                "Cannot set attributes to a strict '{cls}' object.".format(
                    cls=type(self).__name__
                )
            )
        else:
            return super(type(self), self).__setattr__(name, value)


@Singleton
class APIConnection(object):
    """轻量 API 连接器（旧版入口，保留兼容）。"""

    QUERY_DOMAIN = "https://api.steampowered.com"
    # Use double curly-braces to tell Python that these variables shouldn't be
    # expanded yet.
    QUERY_TEMPLATE = "{domain}/{{interface}}/{{command}}/{{version}}/".format(
        domain=QUERY_DOMAIN
    )

    def __init__(
        self,
        api_key: tp.Optional[str] = None,
        settings: tp.Optional[tp.Dict[str, tp.Any]] = None,
        validate_key: bool = False,
    ):
        """
        单例连接器：用于简单场景的直接调用。

        注意：APIConnection 将很快被 APIInterface 弃用。

        初始化主 APIConnection。由于 APIConnection 是单例对象，任何进一步的"初始化"
        都不会重新初始化实例，而只是检索现有实例。要重新分配 API 密钥，
        请检索单例实例并使用密钥调用 "reset"。

        :param api_key: Steam Web API 密钥。（可选，但推荐）
        :param settings: 高级调整的字典。小心！（可选）
            precache -- True/False。（默认：True）决定检索一组用户的属性，如 "friends"，
                        是否应预缓存玩家摘要，如昵称。如果您计划立即使用昵称，则推荐使用此选项，
                        因为缓存是批量进行的，而逐个检索需要一段时间。
        :param validate_key: 使用给定密钥对 API 执行测试调用，以确保密钥有效且正常工作。

        """
        self.reset(api_key)

        self.precache = True

        if settings is None:
            settings = dict()

        if "precache" in settings and issubclass(type(settings["precache"]), bool):
            self.precache = settings["precache"]

        if validate_key:
            if api_key is None:
                raise ValueError('"validate_key" is True, but no key was given.')

            # Call "GetSupportedAPIList", which is guaranteed to succeed with
            # any valid key. (Or no key)
            try:
                self.call("ISteamWebAPIUtil", "GetSupportedAPIList", "v1")
            except (APIUnauthorized, APIKeyRequired, APIPrivate):
                raise APIConfigurationError("This API key is invalid.")

    def reset(self, api_key: tp.Optional[str]) -> None:
        """重置连接器使用的 API Key。"""
        self._api_key = api_key

    def call(
        self,
        interface: str,
        command: str,
        version: str,
        method: str = GET,
        **kwargs: tp.Any,
    ) -> tp.Optional["APIResponse"]:
        """
        直接调用指定接口/命令/版本，自动处理 key 与格式。

        调用 API 命令。method 之后的所有关键字命令都将自动转换为基于 GET/POST 的命令。

        :param interface: 包含请求命令的接口名称。（例如："ISteamUser"）
        :param command: 匹配的命令。（例如："GetPlayerSummaries"）
        :param version: 您正在使用的此 API 的版本。（通常是 v000X 或 vX，其中 "X" 代表一个数字）
        :param method: 此调用应使用的 HTTP 方法。默认为 GET，但可以覆盖为 POST，
                       用于仅限 POST 的 API 或长参数列表。
        :param kwargs: 调用本身的一堆关键字参数。不应指定 "key" 和 "format"。
                       如果 APIConnection 有关联的密钥，"key" 将被其覆盖，覆盖 "format"
                       会取消自动解析。（结果对象将不是 APIResponse 而是字符串。）

        :rtype: APIResponse
        """
        for argument in kwargs:
            if isinstance(kwargs[argument], list):
                # 该API以“a,b,c”的结构接收多个值，因此我们必须以这种方式对其进行编码。
                kwargs[argument] = ",".join(kwargs[argument])
            elif isinstance(kwargs[argument], bool):
                # 该API将True/False视为1/0。请进行转换。
                if kwargs[argument] is True:
                    kwargs[argument] = 1
                else:
                    kwargs[argument] = 0

        automatic_parsing = True
        if "format" in kwargs:
            automatic_parsing = False
        else:
            kwargs["format"] = "json"

        if self._api_key is not None:
            kwargs["key"] = self._api_key

        query = self.QUERY_TEMPLATE.format(
            interface=interface, command=command, version=version
        )

        if method == POST:
            response = requests.request(method, query, data=kwargs)
        else:
            response = requests.request(method, query, params=kwargs)

        errors.check(response)

        if automatic_parsing is True:
            response_obj = response.json()
            if len(response_obj.keys()) == 1 and "response" in response_obj:
                return APIResponse(response_obj["response"])
            else:
                return APIResponse(response_obj)


class APIResponse(object):
    """
    响应对象包装器：将 dict 包装为可点访问的对象。

    一个字典代理对象，用于将 API 响应对象化，以实现更漂亮的代码、
    更容易的原型设计和更少无意义的调试（"哦，我忘了方括号。"）。

    递归包装每个给它的响应，通过将每个 'dict' 对象替换为
    APIResponse 实例。其他类型是安全的。
    """

    def __init__(self, father_dict: tp.Dict[str, tp.Any]):
        # Initialize an empty dictionary.
        self._real_dictionary = {}
        # Recursively wrap the response in APIResponse instances.
        for item in father_dict:
            if isinstance(father_dict[item], dict):
                self._real_dictionary[item] = APIResponse(father_dict[item])
            elif isinstance(father_dict[item], list):
                self._real_dictionary[item] = APIResponse._wrap_list(father_dict[item])
            else:
                self._real_dictionary[item] = father_dict[item]

    @staticmethod
    def _wrap_list(original_list: tp.List[tp.Any]) -> tp.List[tp.Any]:
        """
        递归包装列表中的 dict 为 APIResponse。

        接收项目列表并递归地将其中的任何字典包装为 APIResponse
        对象。解决问题 #12。

        :param original_list: 需要包装的原始列表。
        :type original_list: list
        :return: 一个几乎相同的列表，其中 "dict" 对象被替换为 APIResponse 对象。
        :rtype: list
        """
        new_list = []
        for item in original_list:
            if isinstance(item, dict):
                new_list += [APIResponse(item)]
            elif isinstance(item, list):
                new_list += [APIResponse._wrap_list(item)]
            else:
                new_list += [item]
        return new_list

    def __repr__(self):
        return dict.__repr__(self._real_dictionary)

    def __getattribute__(self, item: str):
        if item == "__dict__":
            return super(APIResponse, self).__getattribute__("_real_dictionary")
        if item.startswith("_"):
            return super(APIResponse, self).__getattribute__(item)
        else:
            if item in self._real_dictionary:
                return self._real_dictionary[item]
            else:
                raise AttributeError(
                    "'{cls}' has no attribute '{attr}'".format(
                        cls=type(self).__name__, attr=item
                    )
                )

    def __getitem__(self, item: str) -> tp.Any:
        return self._real_dictionary[item]

    def __iter__(self):
        return self._real_dictionary.__iter__()


class SteamObject(object):
    """
    Steam 领域对象基类（User/App/Achievement 等）。

    所有丰富的 Steam 对象的基类。（SteamUser、SteamApp 等）
    """

    _id: tp.Any = None
    _cache: tp.Dict[str, tp.Any] = {}
    name: tp.Any = None

    @property
    def id(self) -> tp.Any:
        return self._id  # “_id”由子类设置。

    def __repr__(self):
        try:
            return '<{clsname} "{name}" ({id})>'.format(
                clsname=self.__class__.__name__,
                name=_sanitize_for_console(self.name),
                id=self._id,
            )
        except (AttributeError, APIException):
            return "<{clsname} ({id})>".format(
                clsname=self.__class__.__name__, id=self._id
            )

    def __eq__(self, other: object) -> bool:
        """
        :type other: SteamObject
        """
        # 使用每个对象的 "hash" 来防止派生类共享
        # 相同 ID 的情况，例如用户和应用，如果使用 ".id" 进行比较，
        # 会导致匹配。
        return hash(self) == hash(other)

    def __ne__(self, other: object) -> bool:
        """
        :type other: SteamObject
        """
        return not self == other

    def __hash__(self) -> int:
        return hash(self.id)


def store(
    obj: tp.Any,
    property_name: str,
    data: tp.Any,
    received_time: float = 0,
) -> None:
    """
    缓存对象属性值，用于 cached_property 与预热。

    将数据存储在支持缓存的对象的缓存中。主要用于预缓存。

    :param obj: 目标对象。
    :type obj: SteamObject
    :param property_name: 目标属性的名称。
    :param data: 我们需要存储在对象缓存中的数据。
    :type data: object
    :param received_time: 检索此数据的时间。用于属性缓存。
    设置为 0 以使用当前时间。
    :type received_time: float
    """
    if received_time == 0:
        received_time = time.time()
    # Just making sure caching is supported for this object...
    if issubclass(type(obj), SteamObject) or hasattr(obj, "_cache"):
        obj._cache[property_name] = (data, received_time)
    else:
        raise TypeError(
            "This object type either doesn't visibly support caching, or has yet to initialise its cache."
        )


def expire(obj: tp.Any, property_name: str) -> None:
    """
    失效指定缓存属性。

    使缓存的属性失效

    :param obj: 目标对象。
    :type obj: SteamObject
    :param property_name:
    :type property_name:
    """
    if issubclass(type(obj), SteamObject) or hasattr(obj, "_cache"):
        del obj._cache[property_name]
    else:
        raise TypeError(
            "This object type either doesn't visibly support caching, or has yet to initialise its cache."
        )


def chunker(seq: tp.Sequence[tp.Any], size: int):
    """
    将序列分块，便于批量请求。

    将可迭代对象转换为可迭代对象的迭代对象，大小为 size

    :param seq: 目标可迭代对象
    :type seq: iterable
    :param size: 结果批次的最大大小
    :type size: int
    :rtype: iterable
    """
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


def _sanitize_for_console(value):
    """将值安全转换为可输出文本（Python3 only）。"""
    if isinstance(value, bytes):
        return value.decode(errors="ignore")
    return value
