"""
Steam 用户相关对象与属性访问

封装玩家信息、好友、游戏库、徽章等数据的获取与缓存。
"""

__author__ = "SmileyBarry"

from .core import APIConnection, SteamObject, chunker

from .app import SteamApp
from .decorators import cached_property, INFINITE, MINUTE, HOUR
from .errors import *

import datetime
import itertools
import typing as tp


class SteamUserBadge(SteamObject):
    def __init__(self, badge_id, level, completion_time, xp, scarcity, appid=None):
        """
        用户徽章对象：由 GetBadges 等接口返回。

        创建一个新的 Steam 用户徽章实例。通常不应初始化此对象，
        而是从诸如 "SteamUser.badges" 之类的属性接收它。

        :param badge_id: 徽章的 ID。不是唯一的实例 ID，而是有助于从用户徽章列表中识别它的 ID。
                         在 API 规范中显示为 `badgeid`。
        :type badge_id: int
        :param level: 徽章的当前等级。
        :type level: int
        :param completion_time: 解锁此徽章的确切时刻。可以是 datetime.datetime 对象或 Unix 时间戳。
        :type completion_time: int 或 datetime.datetime
        :param xp: 此徽章的当前经验值。
        :type xp: int
        :param scarcity: 此徽章的稀有程度。表示拥有它的人数。
        :type scarcity: int
        :param appid: 此徽章关联的应用 ID。
        :type appid: int
        """
        self._badge_id = badge_id
        self._level = level
        if isinstance(completion_time, datetime.datetime):
            self._completion_time = completion_time
        else:
            self._completion_time = datetime.datetime.fromtimestamp(completion_time)
        self._xp = xp
        self._scarcity = scarcity
        self._appid = appid
        if self._appid is not None:
            self._id = self._appid
        else:
            self._id = self._badge_id

    @property
    def badge_id(self):
        return self._badge_id

    @property
    def level(self):
        return self._level

    @property
    def xp(self):
        return self._xp

    @property
    def scarcity(self):
        return self._scarcity

    @property
    def appid(self):
        return self._appid

    @property
    def completion_time(self):
        return self._completion_time

    def __repr__(self):
        return "<{clsname} {id} ({xp} XP)>".format(
            clsname=self.__class__.__name__, id=self._id, xp=self._xp
        )

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of
        # objects wouldn't cause a match.
        return hash((self._appid, self.id))


class SteamGroup(SteamObject):
    def __init__(self, guid):
        """Steam 群组对象，仅持有 GUID。"""
        self._id = guid

    def __hash__(self):
        # Don't just use the ID so ID collision between different types of
        # objects wouldn't cause a match.
        return hash(("group", self.id))

    @property
    def guid(self):
        return self._id


class SteamUser(SteamObject):
    PLAYER_SUMMARIES_BATCH_SIZE = 350
    friend_since: tp.Optional[int] = None

    # OVERRIDES
    def __init__(
        self,
        userid: tp.Optional[tp.Union[int, str]] = None,
        userurl: tp.Optional[str] = None,
        accountid: tp.Optional[int] = None,
    ):
        """
        Steam 用户对象：支持 SteamID64、个性化 URL、AccountID 初始化。

        创建一个新的 Steam 用户实例。使用此对象检索有关该用户的详细信息。

        :param userid: 用户的 64 位 SteamID。（可选，除非未指定 steam_userurl）
        :type userid: int
        :param userurl: 用户的个性化 URL 结尾名称。（如果未指定 "steam_userid" 则必需，否则不使用）
        :type userurl: str
        :raise: 使用不当时引发 ValueError。
        """
        if userid is None and userurl is None and accountid is None:
            raise ValueError("One of the arguments must be supplied.")

        if userurl is not None:
            if "/" in userurl:
                # This is a full URL. It's not valid.
                raise ValueError(
                    '"userurl" must be the *ending* of a vanity URL, not the entire URL!'
                )
            response = APIConnection().call(
                "ISteamUser", "ResolveVanityURL", "v0001", vanityurl=userurl
            )
            if response.success != 1:
                raise UserNotFoundError("User not found.")
            userid = response.steamid

        if accountid is not None:
            userid = self._convert_accountid_to_steamid(accountid)

        if userid is not None:
            self._id = int(userid)

    def __eq__(self, other):
        if isinstance(other, SteamUser):
            if self.steamid == other.steamid:
                return True
            else:
                return False
        else:
            return super(SteamUser, self).__eq__(other)

    def __str__(self):
        return str(self.name)

    def __hash__(self):
        # 不要只使用ID，这样不同类型对象之间的ID冲突就不会导致匹配。
        return hash(("user", self.id))

    # PRIVATE UTILITIES
    @staticmethod
    def _convert_accountid_to_steamid(accountid: int) -> str:
        """AccountID 转 SteamID64（官方通用算法）。"""
        if accountid % 2 == 0:
            y = 0
            z = accountid / 2
        else:
            y = 1
            z = (accountid - 1) / 2
        return "7656119%d" % (z * 2 + 7960265728 + y)

    @staticmethod
    def _convert_games_list(
        raw_list: tp.List[tp.Any], associated_userid: tp.Optional[int] = None
    ) -> tp.List[SteamApp]:
        """
        将 APIResponse 游戏列表转换为 SteamApp 对象，并补充常用字段。

        将原始的、APIResponse 格式的游戏列表转换为完整的 SteamApp 对象。
        :type raw_list: APIResponse 列表
        :rtype: SteamApp 列表
        """
        games_list = []
        for game in raw_list:
            game_obj = SteamApp.from_api_response(game, associated_userid)
            if "playtime_2weeks" in game:
                game_obj.playtime_2weeks = game.playtime_2weeks
            if "playtime_forever" in game:
                game_obj.playtime_forever = game.playtime_forever
            if "img_logo_url" in game:
                game_obj.img_logo_url = game.img_logo_url
            if "img_icon_url" in game:
                game_obj.img_icon_url = game.img_icon_url
            games_list += [game_obj]
        return games_list

    @cached_property(ttl=2 * HOUR)
    def _summary(self) -> tp.Any:
        """
        玩家基础信息缓存（昵称、头像、在线状态等）。

        :rtype: APIResponse
        """
        return (
            APIConnection()
            .call("ISteamUser", "GetPlayerSummaries", "v0002", steamids=self.steamid)
            .players[0]
        )

    @cached_property(ttl=INFINITE)
    def _bans(self) -> tp.Any:
        """
        封禁信息缓存（VAC/社区封禁）。

        :rtype: APIResponse
        """
        return (
            APIConnection()
            .call("ISteamUser", "GetPlayerBans", "v1", steamids=self.steamid)
            .players[0]
        )

    @cached_property(ttl=30 * MINUTE)
    def _badges(self) -> tp.Any:
        """
        徽章与等级信息缓存。

        :rtype: APIResponse
        """
        return APIConnection().call(
            "IPlayerService", "GetBadges", "v1", steamid=self.steamid
        )

    def _summary_data(self) -> tp.Any:
        return tp.cast(tp.Any, self._summary)

    def _badges_data(self) -> tp.Any:
        return tp.cast(tp.Any, self._badges)

    def _bans_data(self) -> tp.Any:
        return tp.cast(tp.Any, self._bans)

    # PUBLIC ATTRIBUTES
    @property
    def steamid(self):
        """
        :rtype: int
        """
        return self._id

    @cached_property(ttl=INFINITE)
    def name(self):
        """
        玩家昵称（来自 GetPlayerSummaries）。

        :rtype: str
        """
        summary = self._summary_data()
        return summary.personaname

    @cached_property(ttl=INFINITE)
    def real_name(self):
        """
        真实姓名（若用户公开）。

        :rtype: str
        """
        summary = self._summary_data()
        if "realname" in summary:
            return summary.realname
        else:
            return None

    @cached_property(ttl=INFINITE)
    def country_code(self):
        """
        国家代码（可能为空）。

        :rtype: str or NoneType
        """
        summary = self._summary_data()
        return getattr(summary, "loccountrycode", None)

    @cached_property(ttl=10 * MINUTE)
    def currently_playing(self):
        """
        当前正在玩游戏；如果是共享游戏会标记借出者。

        :rtype: SteamApp
        """
        summary = self._summary_data()
        if "gameid" in summary:
            if "gameextrainfo" in summary:
                game_name = summary.gameextrainfo
            else:
                game_name = None
            game = SteamApp(summary.gameid, game_name)
            owner = APIConnection().call(
                "IPlayerService",
                "IsPlayingSharedGame",
                "v0001",
                steamid=self._id,
                appid_playing=game.appid,
            )
            if owner.lender_steamid is not 0:
                game._owner = owner.lender_steamid
            return game
        else:
            return None

    @property  # Already cached by "_summary".
    def privacy(self):
        """
        隐私级别枚举值（CommunityVisibilityState）。

        :rtype: int or CommunityVisibilityState
        """
        # The Web API is a public-facing interface, so it's very unlikely that it will
        # ever change drastically. (More values could be added, but existing ones wouldn't
        # be changed.)
        summary = self._summary_data()
        return summary.communityvisibilitystate

    @property  # Already cached by "_summary".
    def last_logoff(self):
        """
        最后离线时间（时间戳转 datetime）。

        :rtype: datetime
        """
        summary = self._summary_data()
        return datetime.datetime.fromtimestamp(summary.lastlogoff)

    @cached_property(ttl=INFINITE)  # Already cached, but never changes.
    def time_created(self):
        """
        账号创建时间（时间戳转 datetime）。

        :rtype: datetime
        """
        summary = self._summary_data()
        return datetime.datetime.fromtimestamp(summary.timecreated)

    @cached_property(ttl=INFINITE)  # Already cached, but unlikely to change.
    def profile_url(self):
        """
        个人资料 URL。

        :rtype: str
        """
        summary = self._summary_data()
        return summary.profileurl

    @property  # Already cached by "_summary".
    def avatar(self):
        """
        小尺寸头像 URL。

        :rtype: str
        """
        summary = self._summary_data()
        return summary.avatar

    @property  # Already cached by "_summary".
    def avatar_medium(self):
        """
        中尺寸头像 URL。

        :rtype: str
        """
        summary = self._summary_data()
        return summary.avatarmedium

    @property  # Already cached by "_summary".
    def avatar_full(self):
        """
        大尺寸头像 URL。

        :rtype: str
        """
        summary = self._summary_data()
        return summary.avatarfull

    @property  # Already cached by "_summary".
    def state(self):
        """
        在线状态枚举值（OnlineState）。

        :rtype: int or OnlineState
        """
        summary = self._summary_data()
        return summary.personastate

    @cached_property(ttl=1 * HOUR)
    def groups(self):
        """
        所在群组列表。

        :rtype: list of SteamGroup
        """
        response = APIConnection().call(
            "ISteamUser", "GetUserGroupList", "v1", steamid=self.steamid
        )
        group_list = []
        for group in response.groups:
            group_obj = SteamGroup(group.gid)
            group_list += [group_obj]
        return group_list

    @cached_property(ttl=1 * HOUR)
    def group(self):
        """
        主群组（primaryclanid）。

        :rtype: SteamGroup
        """
        summary = self._summary_data()
        return SteamGroup(summary.primaryclanid)

    @cached_property(ttl=1 * HOUR)
    def friends(self):
        """
        好友列表；可选预取好友摘要以减少后续调用。

        :rtype: list of SteamUser
        """
        import time

        response = APIConnection().call(
            "ISteamUser",
            "GetFriendList",
            "v0001",
            steamid=self.steamid,
            relationship="friend",
        )
        friends_list = []
        for friend in response.friendslist.friends:
            friend_obj = SteamUser(friend.steamid)
            friend_obj.friend_since = friend.friend_since
            friend_obj._cache = {}
            friends_list += [friend_obj]

        # 批量获取好友摘要，减少单个查询次数
        if APIConnection().precache is True:
            # APIConnection() accepts lists of strings as argument values.
            id_player_map = {str(friend.steamid): friend for friend in friends_list}
            ids = list(id_player_map.keys())

            player_details = list(
                itertools.chain.from_iterable(
                    APIConnection()
                    .call(
                        "ISteamUser", "GetPlayerSummaries", "v0002", steamids=id_batch
                    )
                    .players
                    for id_batch in chunker(ids, self.PLAYER_SUMMARIES_BATCH_SIZE)
                )
            )

            now = time.time()
            for player_summary in player_details:
                # Fill in the cache with this info.
                id_player_map[player_summary.steamid]._cache["_summary"] = (
                    player_summary,
                    now,
                )
        return friends_list

    @property  # Already cached by "_badges".
    def level(self):
        """
        玩家等级。

        :rtype: int
        """
        badges = self._badges_data()
        return badges.player_level

    @property  # Already cached by "_badges".
    def badges(self):
        """
        徽章列表。

        :rtype: list of SteamUserBadge
        """
        badge_list = []
        badges = self._badges_data()
        for badge in badges.badges:
            badge_list += [
                SteamUserBadge(
                    badge.badgeid,
                    badge.level,
                    badge.completion_time,
                    badge.xp,
                    badge.scarcity,
                    getattr(badge, "appid", None),
                )
            ]
        return badge_list

    @property  # Already cached by "_badges".
    def xp(self):
        """
        玩家经验值。

        :rtype: int
        """
        badges = self._badges_data()
        return badges.player_xp

    @cached_property(ttl=INFINITE)
    def recently_played(self):
        """
        最近两周游玩游戏列表（私密账户会抛 AccessException）。

        :rtype: list of SteamApp
        """
        response = APIConnection().call(
            "IPlayerService", "GetRecentlyPlayedGames", "v1", steamid=self.steamid
        )
        if "total_count" not in response:
            # 私人资料会引发一种特殊的响应，在这种响应中，API不会告知我们是否存在任何结果。我们只会收到一个空白的JSON文档。
            raise AccessException()
        if response.total_count == 0:
            return []
        return self._convert_games_list(response.games, self._id)

    @cached_property(ttl=INFINITE)
    def games(self):
        """
        完整游戏库（包含免费游戏与应用信息）。

        :rtype: list of SteamApp
        """
        response = APIConnection().call(
            "IPlayerService",
            "GetOwnedGames",
            "v1",
            steamid=self.steamid,
            include_appinfo=True,
            include_played_free_games=True,
        )
        if "game_count" not in response:
            # Private profiles will cause a special response, where the API doesn't tell us if there are
            # any results *at all*. We just get a blank JSON document.
            raise AccessException()
        if response.game_count == 0:
            return []
        return self._convert_games_list(response.games, self._id)

    @cached_property(ttl=INFINITE)
    def owned_games(self):
        """
        仅拥有的付费游戏库（不包含免费游戏）。

        :rtype: list of SteamApp
        """
        response = APIConnection().call(
            "IPlayerService",
            "GetOwnedGames",
            "v1",
            steamid=self.steamid,
            include_appinfo=True,
            include_played_free_games=False,
        )
        if "game_count" not in response:
            # 私人资料会引发一种特殊的响应，在这种响应中，API不会告知我们是否存在任何结果。我们只会收到一个空白的JSON文档。
            raise AccessException()
        if response.game_count == 0:
            return []
        return self._convert_games_list(response.games, self._id)

    @cached_property(ttl=INFINITE)
    def is_vac_banned(self):
        """
        是否 VAC 封禁。

        :rtype: bool
        """
        bans = self._bans_data()
        return bans.VACBanned

    @cached_property(ttl=INFINITE)
    def is_community_banned(self):
        """
        是否社区封禁。

        :rtype: bool
        """
        bans = self._bans_data()
        return bans.CommunityBanned

    @cached_property(ttl=INFINITE)
    def number_of_vac_bans(self):
        """
        VAC 封禁次数。

        :rtype: int
        """
        bans = self._bans_data()
        return bans.NumberOfVACBans

    @cached_property(ttl=INFINITE)
    def days_since_last_ban(self):
        """
        距离上次封禁天数。

        :rtype: int
        """
        bans = self._bans_data()
        return bans.DaysSinceLastBan

    @cached_property(ttl=INFINITE)
    def number_of_game_bans(self):
        """
        游戏封禁次数。

        :rtype: int
        """
        bans = self._bans_data()
        return bans.NumberOfGameBans

    @cached_property(ttl=INFINITE)
    def economy_ban(self):
        """
        经济制裁状态。

        :rtype: str
        """
        bans = self._bans_data()
        return bans.EconomyBan

    @cached_property(ttl=INFINITE)
    def is_game_banned(self):
        """
        是否存在游戏封禁记录。

        :rtype: bool
        """
        bans = self._bans_data()
        return bans.NumberOfGameBans != 0
