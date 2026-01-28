"""
Steam游戏库处理模块
用于从Steam API和Steam商店获取游戏信息
"""

import json
import logging
import os
import re
import typing as tp

import requests

from src.api.steam import steamapi
from src.errors import (
    SteamApiError,
    SteamApiNotFoundError,
    SteamStoreApiError,
    NetworkError,
    DataParseError,
)
from src.models.steam import SteamStoreApp
from src.utils import color, echo, retry, dump_to_file, load_from_file

from .base import GameInfo, GamesLibrary, TGameID

logger = logging.getLogger(__name__)


# 类型别名
TSteamUserID = tp.Union[str, int]  # Steam用户ID类型（字符串或整数）
TSteamApiKey = str  # Steam API密钥类型

PLATFORM = "steam"  # 平台标识符


class SteamStoreApi:
    """
    Steam商店API客户端
    用于从Steam商店获取游戏详细信息
    """

    # Steam商店API端点
    API_HOST = "https://store.steampowered.com/api/appdetails?appids={}"

    def __init__(self):
        """
        初始化Steam商店API客户端
        """
        self.session = requests.Session()  # HTTP会话对象
        self._cache = {}  # 游戏信息缓存

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭session"""
        self.session.close()

    @retry(
        SteamStoreApiError,
        retry_num=2,
        initial_wait=90,
        backoff=1,
        raise_on_error=False,
        debug_msg="Steam商店API请求限制已超出",
        debug=True,
    )
    def get_game_info(self, game_id: TGameID) -> tp.Optional[SteamStoreApp]:
        """
        获取Steam商店中的游戏信息

        Args:
            game_id: 游戏ID

        Returns:
            SteamStoreApp对象或None（如果获取失败）

        Raises:
            SteamApiNotFoundError: 游戏未找到
            SteamStoreApiError: API请求错误
            SteamApiError: 其他API错误
        """
        game_id = str(game_id)
        # 检查缓存
        if game_id in self._cache:
            logger.debug(f"从缓存获取游戏 {game_id}")
            return self._cache[game_id]

        try:
            # 请求Steam商店API
            r = self.session.get(self.API_HOST.format(game_id), timeout=3)
            if not r.ok:
                logger.error(f"Steam Store API 返回错误状态码: {r.status_code}")
                raise SteamStoreApiError(
                    message=f"无法获取 {r.url}, 状态码: {r.status_code}",
                    details={"url": r.url, "status_code": r.status_code},
                    original_exception=None,
                )

            # JSON 解析错误
            try:
                response_data = r.json()
                response_body = response_data.get(str(game_id))
            except json.JSONDecodeError as e:
                logger.error(f"Steam Store API 响应JSON解析失败: {e}")
                raise DataParseError(
                    message="Steam Store API 响应格式错误",
                    details={"game_id": game_id},
                    original_exception=e,
                ) from e

            if not response_body or not response_body.get("success"):
                logger.warning(f"游戏 {game_id} 在Steam商店中未找到或请求失败")
                raise SteamApiNotFoundError(
                    message=f"游戏 {game_id} 请求失败或未找到",
                    details={"game_id": game_id},
                )

            # 解析并缓存游戏信息
            self._cache[game_id] = SteamStoreApp.load(response_body["data"])
            logger.debug(f"成功获取并缓存游戏 {game_id}: {self._cache[game_id].name}")

            return self._cache[game_id]

        except requests.exceptions.Timeout as e:
            logger.error(f"Steam Store API 请求超时: {e}")
            raise NetworkError(
                message=f"Steam Store API 请求超时",
                details={"game_id": game_id},
                original_exception=e,
            ) from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Steam Store API 连接失败: {e}")
            raise NetworkError(
                message=f"Steam Store API 连接失败",
                details={"game_id": game_id},
                original_exception=e,
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Steam Store API 请求异常: {e}")
            raise NetworkError(
                message=f"Steam Store API 请求失败: {e}",
                details={"game_id": game_id},
                original_exception=e,
            ) from e
        except (
            SteamApiNotFoundError,
            SteamStoreApiError,
            DataParseError,
            NetworkError,
        ):
            raise
        except KeyError as e:
            logger.error(f"Steam Store API 响应数据格式错误: {e}")
            raise DataParseError(
                message=f"Steam Store API 响应数据格式错误",
                details={"game_id": game_id},
                original_exception=e,
            ) from e
        except Exception as e:
            logger.exception(f"获取游戏 {game_id} 信息时发生未知错误: {e}")
            raise SteamApiError(
                message=f"获取游戏信息失败: {e}",
                details={"game_id": game_id},
                original_exception=e,
            ) from e


class SteamGamesLibrary(GamesLibrary):
    """
    Steam游戏库管理类
    继承自GamesLibrary，实现Steam平台特定的游戏库操作
    """

    # Steam图片资源主机地址
    IMAGE_HOST = "http://media.steampowered.com/steamcommunity/public/images/apps/"
    # 游戏信息缓存文件名
    CACHE_GAME_FILE = "game_info_cache.json"

    def __init__(self, api_key: TSteamApiKey, user_id: TSteamUserID):
        """
        初始化Steam游戏库

        Args:
            api_key: Steam API密钥
            user_id: Steam用户ID
        """
        self.api = self._get_api(api_key)  # Steam API连接对象
        self.store = SteamStoreApi()  # Steam商店API客户端
        self.user = self._get_user(user_id)  # Steam用户对象
        self._games = {}  # 游戏信息字典
        self._store_skipped = []  # 从商店跳过的游戏ID列表

    def _get_api(self, api_key: TSteamApiKey):
        """
        获取Steam API连接对象

        Args:
            api_key: Steam API密钥

        Returns:
            APIConnection对象

        Raises:
            SteamApiError: API连接失败
        """
        try:
            api_connection = steamapi.core.APIConnection(
                api_key=api_key, validate_key=True
            )
            logger.info("Steam API 连接成功")
            return api_connection
        except Exception as e:
            logger.error(f"Steam API 连接失败: {e}")
            raise SteamApiError(
                message=f"Steam API 连接失败: {e}",
                details={"api_key_prefix": api_key[:8] + "****" if api_key else None},
                original_exception=e,
            ) from e

    def _get_user(self, user_id: TSteamUserID):
        """
        获取Steam用户对象

        Args:
            user_id: Steam用户ID（可以是整数ID或字符串URL）

        Returns:
            SteamUser对象

        Raises:
            SteamApiError: 用户未找到或其他错误
        """
        try:
            # 根据user_id类型选择不同的构造方式
            user = (
                steamapi.user.SteamUser(user_id)
                if isinstance(user_id, int)
                else steamapi.user.SteamUser(userurl=user_id)
            )
            logger.info(f"Steam 用户获取成功: {user_id}")
            return user
        except steamapi.errors.UserNotFoundError as e:
            logger.warning(f"Steam 用户未找到: {user_id}")
            raise SteamApiNotFoundError(
                message=f"用户 {user_id} 未找到",
                details={"user_id": user_id},
                original_exception=e,
            ) from e
        except Exception as e:
            logger.error(f"获取 Steam 用户失败: {e}")
            raise SteamApiError(
                message=f"获取用户信息失败: {e}",
                details={"user_id": str(user_id)},
                original_exception=e,
            ) from e

    @classmethod
    def login(
        cls,
        api_key: tp.Optional[TSteamApiKey] = None,
        user_id: tp.Optional[TSteamUserID] = None,
    ):
        """
        登录Steam（类方法）
        如果未提供凭证，会从环境变量读取，如果环境变量也没有则提示用户输入

        Args:
            api_key: Steam API密钥（可选），如果为None则从环境变量 STEAM_TOKEN 读取
            user_id: Steam用户ID（可选），如果为None则从环境变量 STEAM_USER 读取

        Returns:
            SteamGamesLibrary实例
        """
        # 从环境变量读取 api_key
        if api_key is None:
            api_key = os.getenv("STEAM_TOKEN")
            if not api_key:
                echo(
                    color.y("从以下地址获取Steam令牌: ")
                    + "https://steamcommunity.com/dev/apikey"
                )
                api_key = input(color.c("Token: ")).strip()

        # 从环境变量读取 user_id
        if user_id is None:
            user_id_str = os.getenv("STEAM_USER")
            if user_id_str:
                # 处理环境变量中的 user_id（支持数字ID或自定义URL）
                user_id_str = user_id_str.strip()
                # 如果是纯数字，转换为整数（Steam 64位ID）
                if user_id_str.isdigit():
                    user_id = int(user_id_str)
                else:
                    # 否则作为自定义URL处理（移除URL前缀）
                    user_id = re.sub(
                        r"^https?:\/\/steamcommunity\.com\/id\/", "", user_id_str
                    )
            else:
                # 如果环境变量也没有，提示用户输入
                echo.y("请输入Steam用户个人资料ID。")
                user_id = input(
                    color.c("User: http://steamcommunity.com/profiles/")
                ).strip()
                # 移除URL前缀，只保留用户ID
                user_id = re.sub(r"^https?:\/\/steamcommunity\.com\/id\/", "", user_id)

        return cls(api_key=api_key, user_id=user_id)

    def _image_link(self, game_id: TGameID, img_hash: str):
        """
        生成Steam游戏图片链接

        Args:
            game_id: 游戏ID
            img_hash: 图片哈希值

        Returns:
            str: 完整的图片URL
        """
        return self.IMAGE_HOST + f"{game_id}/{img_hash}.jpg"

    @staticmethod
    def _playtime_format(playtime_in_minutes: int) -> str:
        """
        格式化游戏时长

        Args:
            playtime_in_minutes: 游戏时长（分钟）

        Returns:
            str: 格式化后的游戏时长字符串
        """
        if playtime_in_minutes == 0:
            return "从未游玩"
        if playtime_in_minutes < 120:
            return f"{playtime_in_minutes} 分钟"
        return f"{playtime_in_minutes // 60} 小时"

    def _cache_game(self, game_info: GameInfo):
        """
        将游戏信息缓存到文件

        Args:
            game_info: 游戏信息对象
        """
        g = load_from_file(self.CACHE_GAME_FILE)
        g[str(game_info.id)] = game_info.to_dict()
        dump_to_file(g, self.CACHE_GAME_FILE)

    def _load_cached_games(self, skip_free_games: bool = False):
        """
        从缓存文件加载游戏信息

        Args:
            skip_free_games: 是否跳过免费游戏
        """
        g = load_from_file(self.CACHE_GAME_FILE)
        for id_, game_dict in g.items():
            game_info = GameInfo(**game_dict)
            if skip_free_games and game_info.free:
                continue
            self._games[id_] = game_info

    def _fetch_library_games(
        self,
        skip_non_steam: bool = False,
        skip_free_games: bool = False,
        library_only: bool = False,
        force: bool = False,
        limit: tp.Optional[int] = None,
    ):
        """
        从Steam游戏库获取游戏信息

        Args:
            skip_non_steam: 是否跳过Steam商店中已下架的游戏
            skip_free_games: 是否跳过免费游戏
            library_only: 是否仅从游戏库获取信息（不使用商店API）
            force: 是否强制重新获取
            limit: 限制获取的游戏数量（用于测试，None表示不限制）

        Raises:
            SteamApiError: API请求错误
        """
        # 如果已有缓存且不强制刷新，直接返回
        if self._games and not force:
            return

        if force or not self._games:
            self._load_cached_games(skip_free_games=skip_free_games)

        # 再次检查缓存，避免重复获取
        if self._games and not force:
            return

        @retry(
            SteamApiError,
            retry_num=3,
            initial_wait=5,
            backoff=2,
            raise_on_error=True,
            debug_msg="获取Steam游戏库时出错，正在重试...",
            debug=True,
        )
        def _fetch_games():
            if skip_free_games:
                games_iter = self.user.owned_games
            else:
                games_iter = self.user.games

            number_of_games = len(games_iter)
            initial_count = len(self._games)
            if limit is not None and limit > 0 and initial_count >= limit:
                echo.y(
                    f"\n测试模式：缓存中已有 {initial_count} 个游戏（限制：{limit}），跳过获取"
                )
                return

            for i, g in enumerate(sorted(games_iter, key=lambda x: x.name)):
                if limit is not None and limit > 0 and len(self._games) >= limit:
                    echo.y(f"\n测试模式：已获取 {limit} 个游戏，停止获取")
                    break

                game_id = str(g.id)
                if game_id in self._games:
                    continue
                echo.c(
                    " " * 100 + f"\r正在获取 [{i}/{number_of_games}]: {g.name}",
                    end="\r",
                )

                steam_game = None
                if not library_only:
                    try:
                        steam_game = self.store.get_game_info(game_id)
                    except SteamApiNotFoundError:
                        pass

                    if steam_game is None and skip_non_steam:
                        echo.m(f"游戏 {g.name} id:{game_id} 在Steam商店中未找到，跳过")
                        self._store_skipped.append(game_id)
                        continue

                    if steam_game is None:
                        echo.r(
                            f"游戏 {g.name} id:{game_id} 在Steam商店中未找到，从游戏库获取详细信息"
                        )

                logo_uri = None
                if steam_game is not None and steam_game.header_image:
                    logo_uri = steam_game.header_image
                elif getattr(g, "img_logo_url", None):
                    logo_uri = self._image_link(game_id, g.img_logo_url)

                game_info = GameInfo(
                    id=game_id,
                    name=g.name,
                    platforms=[PLATFORM],
                    release_date=(
                        steam_game.release_date.date
                        if steam_game is not None and steam_game.release_date
                        else None
                    ),
                    playtime=(
                        self._playtime_format(g.playtime_forever)
                        if getattr(g, "playtime_forever", None) is not None
                        else None
                    ),
                    playtime_minutes=(
                        g.playtime_forever
                        if getattr(g, "playtime_forever", None) is not None
                        else None
                    ),
                    logo_uri=logo_uri,
                    bg_uri=None,
                    icon_uri=(
                        self._image_link(game_id, g.img_icon_url)
                        if getattr(g, "img_icon_url", None) is not None
                        else None
                    ),
                    free=steam_game.is_free if steam_game is not None else False,
                )
                # 没有打开跳过免费游戏选项，或者游戏不是免费的，缓存游戏信息
                if not (skip_free_games and game_info.free):
                    self._cache_game(game_info)
                # 打开跳过免费游戏选项后并且游戏是免费的，跳过
                if skip_free_games and game_info.free:
                    continue
                self._games[game_id] = game_info

        try:
            _fetch_games()
        except Exception as e:
            raise SteamApiError(
                message=f"获取游戏库失败: {e}",
                original_exception=e,
            ) from e

    def get_games_list(self, **kwargs) -> tp.List[TGameID]:
        """
        获取游戏ID列表

        Args:
            **kwargs: 传递给_fetch_library_games的参数

        Returns:
            List[TGameID]: 游戏ID列表
        """
        self._fetch_library_games(**kwargs)
        return list(self._games)

    def get_game_info(self, game_id: TGameID, **kwargs) -> GameInfo:
        """
        根据游戏ID获取游戏信息

        Args:
            game_id: 游戏ID
            **kwargs: 传递给_fetch_library_games的参数

        Returns:
            GameInfo: 游戏信息对象

        Raises:
            SteamApiError: 游戏未找到
        """
        self._fetch_library_games(**kwargs)

        if game_id not in self._games:
            raise SteamApiError(message=f"未找到ID为 {game_id} 的游戏")

        return self._games[game_id]
