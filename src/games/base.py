"""
游戏库基础模块
定义游戏信息类和游戏库抽象基类
"""

import typing as tp

from abc import abstractmethod, ABCMeta

# 游戏ID类型：可以是整数或字符串
TGameID = tp.Union[int, str]


class GameInfo:
    """
    游戏信息数据类
    存储游戏的基本信息，如名称、平台、发布日期、游戏时长等
    """

    def __init__(
        self,
        id: TGameID,
        name: str,
        platforms: tp.List[str],
        release_date: tp.Optional[str] = None,
        playtime: tp.Optional[str] = None,
        playtime_minutes: tp.Optional[int] = None,
        logo_uri: tp.Optional[str] = None,
        bg_uri: tp.Optional[str] = None,
        icon_uri: tp.Optional[str] = None,
        free: bool = False,
    ):
        """
        初始化游戏信息

        Args:
            id: 游戏唯一标识符
            name: 游戏名称
            platforms: 游戏平台列表
            release_date: 发布日期（字符串格式）
            playtime: 游戏时长（格式化字符串，如"10 小时"）
            playtime_minutes: 游戏时长（分钟数）
            logo_uri: Logo图片URI
            bg_uri: 背景图片URI
            icon_uri: 图标URI
            free: 是否为免费游戏
        """
        self.id = id
        self.name = name
        self.platforms = platforms
        self.release_date = release_date if release_date else None
        self.playtime = playtime if playtime else None
        self.playtime_minutes = playtime_minutes if playtime_minutes else 0
        self.logo_uri = logo_uri if logo_uri else None
        self.bg_uri = bg_uri if bg_uri else None
        self.icon_uri = icon_uri if icon_uri else None
        self.free = free

    def to_dict(self):
        """
        将游戏信息转换为字典

        Returns:
            dict: 游戏信息的字典表示
        """
        return self.__dict__


class GamesLibrary(metaclass=ABCMeta):
    """
    游戏库抽象基类
    定义游戏库必须实现的接口方法
    """

    @abstractmethod
    def get_games_list(self) -> tp.List[TGameID]:
        """
        从游戏库获取游戏ID列表（抽象方法）

        Returns:
            List[TGameID]: 游戏ID列表
        """
        raise NotImplementedError

    @abstractmethod
    def get_game_info(self, game_id: TGameID) -> GameInfo:
        """
        根据游戏ID获取游戏信息（抽象方法）

        Args:
            game_id: 游戏ID

        Returns:
            GameInfo: 游戏信息对象
        """
        raise NotImplementedError
