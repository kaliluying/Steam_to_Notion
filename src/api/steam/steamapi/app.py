"""
Steam 应用与成就对象封装

提供游戏元数据、成就列表与解锁状态的访问。
"""

__author__ = "SmileyBarry"

import typing as tp

from .core import APIConnection, SteamObject, store
from .decorators import cached_property, INFINITE


class SteamApp(SteamObject):
    playtime_2weeks: tp.Optional[int] = None
    playtime_forever: tp.Optional[int] = None
    img_logo_url: tp.Optional[str] = None
    img_icon_url: tp.Optional[str] = None

    def __init__(
        self,
        appid: int,
        name: tp.Optional[str] = None,
        owner: tp.Optional[int] = None,
    ):
        """Steam 应用对象，必要时缓存名称。"""
        self._id = appid
        if name is not None:
            import time

            self._cache = dict()
            self._cache["name"] = (name, time.time())
        # 通常，关联的 userid 也是所有者。
        # 但如果是借来的游戏，情况就不是这样了。在这种情况下，对象创建者
        # 通常会相应地定义属性。然而，此时我们无法询问 API "这是
        # 借来的游戏吗？"，除非它是当前正在玩的游戏，所以这种区别不是在
        # 对象的上下文中完成的，而是在对象创建者的上下文中完成的。
        self._owner = owner
        self._userid = self._owner

    # Factory methods
    @staticmethod
    def from_api_response(
        api_json: tp.Any, associated_userid: tp.Optional[int] = None
    ) -> "SteamApp":
        """
        从 APIResponse 构建 SteamApp 实例。

        从 APIResponse 对象创建一个新的 SteamApp 实例。

        :param api_json: API 返回的原始 JSON，采用 "APIResponse" 形式。
        :type api_json: steamapi.core.APIResponse
        :param associated_userid: 与此游戏关联的用户 ID（如果适用）。这可以是玩过该
                                  应用/游戏的用户，或者如果是借来的游戏，则是其所有者，具体取决于上下文。
        :type associated_userid: long
        :return: 一个新的 SteamApp 实例
        :rtype: SteamApp
        """
        if "appid" not in api_json:
            # An app ID is a bare minimum.
            raise ValueError("创建SteamApp对象需要一个应用程序ID。")

        appid = api_json.appid
        name = None
        if "name" in api_json:
            name = api_json.name

        return SteamApp(appid, name, associated_userid)

    @cached_property(ttl=INFINITE)
    def _schema(self) -> tp.Any:
        """获取游戏 Schema（成就与统计定义）。"""
        return APIConnection().call(
            "ISteamUserStats", "GetSchemaForGame", "v2", appid=self._id
        )

    @property
    def appid(self):
        return self._id

    @cached_property(ttl=INFINITE)
    def achievements(self) -> tp.List["SteamAchievement"]:
        """获取成就列表并填充全局百分比与用户解锁状态。"""
        global_percentages = APIConnection().call(
            "ISteamUserStats",
            "GetGlobalAchievementPercentagesForApp",
            "v0002",
            gameid=self._id,
        )
        if self._userid is not None:
            # Ah-ha, this game is associated to a user!
            userid = self._userid
            unlocks = APIConnection().call(
                "ISteamUserStats",
                "GetUserStatsForGame",
                "v2",
                appid=self._id,
                steamid=userid,
            )
            if "achievements" in unlocks.playerstats:
                unlocks = [
                    associated_achievement.name
                    for associated_achievement in unlocks.playerstats.achievements
                    if associated_achievement.achieved != 0
                ]
        else:
            userid = None
            unlocks = None
        achievements_list = []
        schema = tp.cast(tp.Any, self._schema)
        if "availableGameStats" not in schema.game:
            # No stat data -- at all. This is a hidden app.
            return achievements_list
        for achievement in schema.game.availableGameStats.achievements:
            achievement_obj = SteamAchievement(
                self._id, achievement.name, achievement.displayName, userid
            )
            achievement_obj._cache = {}
            if achievement.hidden == 0:
                store(achievement_obj, "is_hidden", False)
            else:
                store(achievement_obj, "is_hidden", True)
            for (
                global_achievement
            ) in global_percentages.achievementpercentages.achievements:
                if global_achievement.name == achievement.name:
                    achievement_obj.unlock_percentage = global_achievement.percent
            achievements_list += [achievement_obj]
        if unlocks is not None:
            for achievement in achievements_list:
                if achievement.apiname in unlocks:
                    store(achievement, "is_achieved", True)
                else:
                    store(achievement, "is_achieved", False)
        return achievements_list

    @cached_property(ttl=INFINITE)
    def name(self):
        """游戏名称（来自 Schema）。"""
        schema = tp.cast(tp.Any, self._schema)
        if "gameName" in schema.game:
            return schema.game.gameName
        else:
            return "<Unknown>"

    @cached_property(ttl=INFINITE)
    def owner(self):
        """所有者 SteamID（借用游戏时与 userid 可能不同）。"""
        if self._owner is None:
            return self._userid
        else:
            return self._owner

    def __str__(self):
        return str(self.name)

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of
        # objects wouldn't cause a match.
        return hash(("app", self.id))


class SteamAchievement(SteamObject):
    def __init__(
        self,
        linked_appid: int,
        apiname: str,
        displayname: str,
        linked_userid: tp.Optional[int] = None,
    ):
        """
        成就对象：包含显示名、API 名称、关联用户等信息。

        初始化一个新的 SteamAchievement 实例。您不应该自己创建一个，
        而应该从 "SteamApp.achievements" 创建。

        :param linked_appid: 与此成就关联的 AppID。
        :type linked_appid: int
        :param apiname: 此成就的基于 API 的名称。通常是一个字符串。
        :type apiname: str
        :param displayname: 成就的用户可见名称。
        :type displayname: str
        :param linked_userid: 此成就关联的用户 ID。
        :type linked_userid: int
        :return: 一个新的 SteamAchievement 实例。
        """
        self._appid = linked_appid
        self._id = apiname
        self._displayname = displayname
        self._userid = linked_userid
        self.unlock_percentage = 0.0

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of
        # objects wouldn't cause a match.
        return hash((self.id, self._appid))

    @property
    def appid(self):
        return self._appid

    @property
    def name(self):
        return self._displayname

    @property
    def apiname(self):
        return self._id

    @cached_property(ttl=INFINITE)
    def is_hidden(self) -> tp.Optional[bool]:
        """成就是否隐藏（从 Schema 查询）。"""
        response = APIConnection().call(
            "ISteamUserStats", "GetSchemaForGame", "v2", appid=self._appid
        )
        for achievement in response.game.availableGameStats.achievements:
            if achievement.name == self._id:
                if achievement.hidden == 0:
                    return False
                else:
                    return True

    @cached_property(ttl=INFINITE)
    def is_unlocked(self) -> bool:
        """成就是否已解锁（需要关联用户）。"""
        if self._userid is None:
            raise ValueError("No Steam ID linked to this achievement!")
        response = APIConnection().call(
            "ISteamUserStats",
            "GetPlayerAchievements",
            "v1",
            steamid=self._userid,
            appid=self._appid,
            l="English",
        )
        for achievement in response.playerstats.achievements:
            if achievement.apiname == self._id:
                if achievement.achieved == 1:
                    return True
                else:
                    return False
        # Cannot be found.
        return False
