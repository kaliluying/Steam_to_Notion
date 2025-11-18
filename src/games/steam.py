"""
Steam游戏库处理模块
用于从Steam API和Steam商店获取游戏信息
"""

import re
import typing as tp

import requests

from src.api.steam import steamapi
from src.core import is_valid_link
from src.errors import SteamApiError, SteamApiNotFoundError, SteamStoreApiError
from src.models.steam import SteamStoreApp
from src.utils import color, echo, retry, dump_to_file, load_from_file

from .base import GameInfo, GamesLibrary, TGameID


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
            return self._cache[game_id]
        try:
            # 请求Steam商店API
            r = self.session.get(self.API_HOST.format(game_id), timeout=3)
            if not r.ok:
                raise SteamStoreApiError(
                    f"无法获取 {r.url}, 状态码: {r.status_code}, 响应: {r.text}"
                )

            response_body = r.json()[str(game_id)]
            if not response_body["success"]:
                raise SteamApiNotFoundError(f"游戏 {game_id} 请求失败")

            # 解析并缓存游戏信息
            self._cache[game_id] = SteamStoreApp.load(response_body["data"])

            return self._cache[game_id]
        except (SteamApiNotFoundError, SteamStoreApiError):
            raise
        except Exception as e:
            raise SteamApiError(error=e)


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
            return steamapi.core.APIConnection(api_key=api_key, validate_key=True)
        except Exception as e:
            raise SteamApiError(error=e)

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
            return (
                steamapi.user.SteamUser(user_id)
                if isinstance(user_id, int)
                else steamapi.user.SteamUser(userurl=user_id)
            )
        except steamapi.errors.UserNotFoundError:
            raise SteamApiError(msg=f"用户 {user_id} 未找到")
        except Exception as e:
            raise SteamApiError(error=e)

    @classmethod
    def login(
        cls,
        api_key: tp.Optional[TSteamApiKey] = None,
        user_id: tp.Optional[TSteamUserID] = None,
    ):
        """
        登录Steam（类方法）
        如果未提供凭证，会提示用户输入

        Args:
            api_key: Steam API密钥（可选）
            user_id: Steam用户ID（可选）

        Returns:
            SteamGamesLibrary实例
        """
        # TODO: 从个人资料URL解析游戏库？
        if api_key is None:
            echo(
                color.y("从以下地址获取Steam令牌: ")
                + "https://steamcommunity.com/dev/apikey"
            )
            api_key = input(color.c("Token: ")).strip()
        if user_id is None:
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

    def _get_bg_image(self, game_id: TGameID) -> tp.Optional[str]:
        """
        获取游戏背景图片URL
        尝试多种可能的背景图片路径

        Args:
            game_id: 游戏ID

        Returns:
            str: 背景图片URL，如果不存在则返回None
        """
        _bg_img = "https://steamcdn-a.akamaihd.net/steam/apps/{game_id}/{bg}.jpg"
        # 尝试第一种背景图片路径
        bg_link = _bg_img.format(game_id=game_id, bg="page.bg")
        if is_valid_link(bg_link):
            return bg_link
        # 尝试第二种背景图片路径
        bg_link = _bg_img.format(game_id=game_id, bg="page_bg_generated")
        if is_valid_link(bg_link):
            return bg_link
        return None

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
        cache: bool = True,
        force: bool = False,
        limit: tp.Optional[int] = None,
    ):
        """
        从Steam游戏库获取游戏信息

        Args:
            skip_non_steam: 是否跳过Steam商店中已下架的游戏
            skip_free_games: 是否跳过免费游戏
            library_only: 是否仅从游戏库获取信息（不使用商店API）
            cache: 是否使用缓存
            force: 是否强制重新获取
            limit: 限制获取的游戏数量（用于测试，None表示不限制）

        Raises:
            SteamApiError: API请求错误
        """
        if force or not self._games:
            # 从缓存加载游戏信息
            if cache:
                self._load_cached_games(skip_free_games=skip_free_games)
            try:
                # INSERT_YOUR_CODE
                # 跳过免费游戏时，使用self.user.owned_games，否则用self.user.games
                if skip_free_games:
                    games_iter = self.user.owned_games
                else:
                    games_iter = self.user.games

                number_of_games = len(games_iter)
                # 计算已获取的游戏数量（包括缓存中的）
                initial_count = len(self._games)
                # 如果设置了限制且缓存中的游戏已经达到或超过限制，直接返回
                if limit is not None and limit > 0 and initial_count >= limit:
                    echo.y(
                        f"\n测试模式：缓存中已有 {initial_count} 个游戏（限制：{limit}），跳过获取"
                    )
                    return

                # 遍历用户游戏库中的游戏
                for i, g in enumerate(sorted(games_iter, key=lambda x: x.name)):
                    # 如果设置了限制且已达到限制，停止获取
                    if limit is not None and limit > 0 and len(self._games) >= limit:
                        echo.y(f"\n测试模式：已获取 {limit} 个游戏，停止获取")
                        break

                    game_id = str(g.id)
                    # 如果游戏已在缓存中，跳过
                    if game_id in self._games:
                        continue
                    echo.c(
                        " " * 100 + f"\r正在获取 [{i}/{number_of_games}]: {g.name}",
                        end="\r",
                    )
                    steam_game = None
                    if not library_only:
                        # 从Steam商店获取游戏信息
                        try:
                            steam_game = self.store.get_game_info(game_id)
                        except SteamApiNotFoundError:
                            pass

                        # 如果游戏不在商店中且设置了跳过选项
                        if steam_game is None and skip_non_steam:
                            echo.m(
                                f"游戏 {g.name} id:{game_id} 在Steam商店中未找到，跳过"
                            )
                            self._store_skipped.append(game_id)
                            continue

                        # 如果游戏不在商店中
                        if steam_game is None:
                            echo.r(
                                f"游戏 {g.name} id:{game_id} 在Steam商店中未找到，从游戏库获取详细信息"
                            )

                    # 确定Logo URI
                    logo_uri = None
                    if steam_game is not None and steam_game.header_image:
                        logo_uri = steam_game.header_image
                    elif getattr(g, "img_logo_url", None):
                        logo_uri = self._image_link(game_id, g.img_logo_url)

                    # 创建游戏信息对象
                    game_info = GameInfo(
                        id=game_id,
                        name=g.name,
                        platforms=[PLATFORM],
                        release_date=(
                            steam_game.release_date.date
                            if steam_game is not None
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
                        bg_uri=self._get_bg_image(game_id),
                        icon_uri=(
                            self._image_link(game_id, g.img_icon_url)
                            if getattr(g, "img_icon_url", None) is not None
                            else None
                        ),
                        free=steam_game.is_free if steam_game is not None else None,
                    )
                    # 如果从商店获取到信息，则缓存
                    if steam_game is not None:
                        self._cache_game(game_info)
                    # 如果设置了跳过免费游戏且游戏是免费的，则跳过
                    if skip_free_games and game_info.free:
                        continue
                    self._games[game_id] = game_info
                    # 检查是否达到限制（每次添加后检查）
                    if limit is not None and limit > 0 and len(self._games) >= limit:
                        echo.y(f"\n测试模式：已获取 {limit} 个游戏，停止获取")
                        break
            except Exception as e:
                raise SteamApiError(error=e)

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
            raise SteamApiError(msg=f"未找到ID为 {game_id} 的游戏")

        return self._games[game_id]
