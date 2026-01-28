"""Live Steam Web API smoke test.

Runs real HTTP calls and prints raw responses. Requires valid API key and
identifiers. This file does NOT mock anything and should be run manually.

以下输出内容为实际API响应数据，用于测试Steam Web API接口功能。
输出内容包括：
- ISteamUser: 用户信息、封禁状态、好友列表等
- IPlayerService: 徽章、游戏状态、拥有游戏等
- ISteamUserStats: 游戏成就、统计数据等
- ISteamWebAPIUtil: 支持的API列表等

注意：以下JSON数据为实际API调用结果，包含敏感信息（如Steam ID、API密钥等）。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from steamapi.core import APIConnection, APIResponse


def _env(name: str, required: bool = True) -> str:
    """Fetch environment variable or exit with a helpful message."""

    value = os.getenv(name, "").strip()
    if required and not value:
        print(f"Missing env var: {name}")
        sys.exit(2)
    return value


def _to_plain(value: Any) -> Any:
    """Convert APIResponse objects to plain dicts/lists for JSON output."""

    if isinstance(value, APIResponse):
        return {key: _to_plain(item) for key, item in value.__dict__.items()}
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    return value


def _print(title: str, payload: Any) -> None:
    """Pretty-print API payloads for quick inspection."""

    print("\n" + "=" * 80)
    print(title)
    print("-" * 80)
    print(json.dumps(_to_plain(payload), ensure_ascii=False, indent=2, sort_keys=True))


def main() -> None:
    # Required inputs for live API calls
    api_key = "7F3A5809AC582B9BD88FF780D87553E5"
    steamid = "76561199077366346"
    appid = "812140"
    vanity = _env("STEAM_TEST_VANITY", required=False)

    # Create connection with key (no mocks)
    conn = APIConnection(api_key=api_key)

    # ISteamUser
    if vanity:
        _print(
            "ISteamUser.ResolveVanityURL",
            conn.call("ISteamUser", "ResolveVanityURL", "v0001", vanityurl=vanity),
        )
    _print(
        "ISteamUser.GetPlayerSummaries",
        conn.call("ISteamUser", "GetPlayerSummaries", "v0002", steamids=steamid),
    )
    _print(
        "ISteamUser.GetPlayerBans",
        conn.call("ISteamUser", "GetPlayerBans", "v1", steamids=steamid),
    )
    _print(
        "ISteamUser.GetUserGroupList",
        conn.call("ISteamUser", "GetUserGroupList", "v1", steamid=steamid),
    )
    _print(
        "ISteamUser.GetFriendList",
        conn.call("ISteamUser", "GetFriendList", "v0001", steamid=steamid),
    )

    # IPlayerService
    _print(
        "IPlayerService.GetBadges",
        conn.call("IPlayerService", "GetBadges", "v1", steamid=steamid),
    )
    _print(
        "IPlayerService.IsPlayingSharedGame",
        conn.call(
            "IPlayerService",
            "IsPlayingSharedGame",
            "v0001",
            steamid=steamid,
            appid_playing=appid,
        ),
    )
    _print(
        "IPlayerService.GetRecentlyPlayedGames",
        conn.call("IPlayerService", "GetRecentlyPlayedGames", "v1", steamid=steamid),
    )
    _print(
        "IPlayerService.GetOwnedGames",
        conn.call(
            "IPlayerService",
            "GetOwnedGames",
            "v1",
            steamid=steamid,
            include_appinfo=True,
            include_played_free_games=True,
        ),
    )

    # ISteamUserStats
    _print(
        "ISteamUserStats.GetSchemaForGame",
        conn.call("ISteamUserStats", "GetSchemaForGame", "v2", appid=appid),
    )
    _print(
        "ISteamUserStats.GetGlobalAchievementPercentagesForApp",
        conn.call(
            "ISteamUserStats",
            "GetGlobalAchievementPercentagesForApp",
            "v0002",
            gameid=appid,
        ),
    )
    _print(
        "ISteamUserStats.GetUserStatsForGame",
        conn.call(
            "ISteamUserStats", "GetUserStatsForGame", "v2", appid=appid, steamid=steamid
        ),
    )
    _print(
        "ISteamUserStats.GetPlayerAchievements",
        conn.call(
            "ISteamUserStats",
            "GetPlayerAchievements",
            "v1",
            appid=appid,
            steamid=steamid,
        ),
    )

    # ISteamWebAPIUtil
    _print(
        "ISteamWebAPIUtil.GetSupportedAPIList",
        conn.call("ISteamWebAPIUtil", "GetSupportedAPIList", "v1"),
    )


if __name__ == "__main__":
    main()


"""
================================================================================
ISteamUser.GetPlayerSummaries
--------------------------------------------------------------------------------
{
  "players": [
    {
      "avatar": "https://avatars.steamstatic.com/e1dde7fe207a397634580d4755f7890ccf24ddd7.jpg",
      "avatarfull": "https://avatars.steamstatic.com/e1dde7fe207a397634580d4755f7890ccf24ddd7_full.jpg",
      "avatarhash": "e1dde7fe207a397634580d4755f7890ccf24ddd7",
      "avatarmedium": "https://avatars.steamstatic.com/e1dde7fe207a397634580d4755f7890ccf24ddd7_medium.jpg",
      "communityvisibilitystate": 3,
      "lastlogoff": 1754012861,
      "personaname": "kali",
      "personastate": 0,
      "personastateflags": 0,
      "primaryclanid": "103582791429521408",
      "profilestate": 1,
      "profileurl": "https://steamcommunity.com/profiles/76561199077366346/",
      "realname": "kali",
      "steamid": "76561199077366346",
      "timecreated": 1595907689
    }
  ]
}

================================================================================
ISteamUser.GetPlayerBans
--------------------------------------------------------------------------------
{
  "players": [
    {
      "CommunityBanned": false,
      "DaysSinceLastBan": 0,
      "EconomyBan": "none",
      "NumberOfGameBans": 0,
      "NumberOfVACBans": 0,
      "SteamId": "76561199077366346",
      "VACBanned": false
    }
  ]
}

================================================================================
ISteamUser.GetUserGroupList
--------------------------------------------------------------------------------
{
  "groups": [],
  "success": true
}

================================================================================
ISteamUser.GetFriendList
--------------------------------------------------------------------------------
{
  "friendslist": {
    "friends": [
      {
        "friend_since": 1669343754,
        "relationship": "friend",
        "steamid": "76561198430412323"
      },
      {
        "friend_since": 1669343793,
        "relationship": "friend",
        "steamid": "76561199023603076"
      },
      {
        "friend_since": 1667276061,
        "relationship": "friend",
        "steamid": "76561199067897868"
      },
      {
        "friend_since": 1691505379,
        "relationship": "friend",
        "steamid": "76561199394547848"
      },
      {
        "friend_since": 1667978932,
        "relationship": "friend",
        "steamid": "76561199420255388"
      },
      {
        "friend_since": 1751558947,
        "relationship": "friend",
        "steamid": "76561199873400870"
      }
    ]
  }
}

================================================================================
IPlayerService.GetBadges
--------------------------------------------------------------------------------
{
  "badges": [
    {
      "badgeid": 13,
      "completion_time": 1769175371,
      "level": 84,
      "scarcity": 24022829,
      "xp": 301
    },
    {
      "badgeid": 69,
      "completion_time": 1765936596,
      "level": 1,
      "scarcity": 23050675,
      "xp": 50
    },
    {
      "badgeid": 2,
      "completion_time": 1744689261,
      "level": 2,
      "scarcity": 28140554,
      "xp": 200
    },
    {
      "badgeid": 68,
      "completion_time": 1734592718,
      "level": 1,
      "scarcity": 36270673,
      "xp": 50
    },
    {
      "badgeid": 67,
      "completion_time": 1732796324,
      "level": 2,
      "scarcity": 4950712,
      "xp": 50
    },
    {
      "badgeid": 66,
      "completion_time": 1703163688,
      "level": 1,
      "scarcity": 39548338,
      "xp": 50
    },
    {
      "badgeid": 64,
      "completion_time": 1672158042,
      "level": 1,
      "scarcity": 78911985,
      "xp": 50
    },
    {
      "badgeid": 63,
      "completion_time": 1669362386,
      "level": 2,
      "scarcity": 3479239,
      "xp": 50
    },
    {
      "badgeid": 1,
      "completion_time": 1595907689,
      "level": 5,
      "scarcity": 230457351,
      "xp": 250
    },
    {
      "appid": 3812610,
      "badgeid": 1,
      "border_color": 0,
      "communityitemid": "34922849582",
      "completion_time": 1750990760,
      "level": 17,
      "scarcity": 156798,
      "xp": 1700
    }
  ],
  "player_level": 18,
  "player_xp": 2751,
  "player_xp_needed_current_level": 2600,
  "player_xp_needed_to_level_up": 49
}

================================================================================
IPlayerService.IsPlayingSharedGame
--------------------------------------------------------------------------------
{}

================================================================================
IPlayerService.GetRecentlyPlayedGames
--------------------------------------------------------------------------------
{
  "games": [
    {
      "appid": 1371980,
      "img_icon_url": "8b383999493fa60adbbda2a5a5714805d9d7c913",
      "name": "No Rest for the Wicked",
      "playtime_2weeks": 1328,
      "playtime_deck_forever": 0,
      "playtime_forever": 1328,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1328
    },
    {
      "appid": 814380,
      "img_icon_url": "2704fb9c5465045d00a5b19a0cb1e9bdabbd15cc",
      "name": "Sekiro™: Shadows Die Twice",
      "playtime_2weeks": 648,
      "playtime_deck_forever": 0,
      "playtime_forever": 1194,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1194
    },
    {
      "appid": 1771300,
      "img_icon_url": "80e8d75b87433627cafd2a1bcbb5b9f5741e2277",
      "name": "Kingdom Come: Deliverance II",
      "playtime_2weeks": 364,
      "playtime_deck_forever": 0,
      "playtime_forever": 2981,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 2981
    },
    {
      "appid": 1340990,
      "img_icon_url": "27e73dd43a02f2703f507f0022adf36de4d45590",
      "name": "Rise of the Ronin",
      "playtime_2weeks": 254,
      "playtime_deck_forever": 0,
      "playtime_forever": 1579,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1579
    },
    {
      "appid": 1245620,
      "img_icon_url": "b6e290dd5a92ce98f89089a207733c70c41a1871",
      "name": "ELDEN RING",
      "playtime_2weeks": 148,
      "playtime_deck_forever": 0,
      "playtime_forever": 6306,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 6306
    },
    {
      "appid": 1942280,
      "img_icon_url": "d9dfcab8f300a9548439f70bef7b5f4e53d0fc28",
      "name": "Brotato",
      "playtime_2weeks": 53,
      "playtime_deck_forever": 0,
      "playtime_forever": 477,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 477
    }
  ],
  "total_count": 6
}
================================================================================
IPlayerService.GetOwnedGames
--------------------------------------------------------------------------------
{
  "game_count": 89,
  "games": [
    {
      "appid": 70,
      "content_descriptorids": [
        2,
        5
      ],
      "img_icon_url": "95be6d131fc61f145797317ca437c9765f24b41c",
      "name": "Half-Life",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 220,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "fcfb366051782b8ebf2aa297f3b746395858cb62",
      "name": "Half-Life 2",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 320,
      "content_descriptorids": [
        2,
        5
      ],
      "img_icon_url": "795e85364189511f4990861b578084deef086cb1",
      "name": "Half-Life 2: Deathmatch",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 360,
      "content_descriptorids": [
        2,
        5
      ],
      "img_icon_url": "40b8a62efff5a9ab356e5c56f5c8b0532c8e1aa3",
      "name": "Half-Life Deathmatch: Source",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 43160,
      "has_community_visible_stats": true,
      "img_icon_url": "7b84b80d2cebe41ba87c59b28e2473d3b33e797d",
      "name": "Metro: Last Light Complete Edition",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 49520,
      "has_community_visible_stats": true,
      "img_icon_url": "a3f4945226e69b6196074df4c776e342d3e5a3be",
      "name": "Borderlands 2",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 105600,
      "has_community_visible_stats": true,
      "img_icon_url": "858961e95fbf869f136e1770d586e0caefd4cfac",
      "name": "Terraria",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 171,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 171,
      "rtime_last_played": 1744544264
    },
    {
      "appid": 226620,
      "has_community_visible_stats": true,
      "img_icon_url": "f4c30e39f4ce6da904793d7c91db59a0a70b8b3a",
      "name": "Desktop Dungeons",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 235900,
      "img_icon_url": "d4fae8dbf49b2d8fda0aa9d74323529e41d200a2",
      "name": "RPG Maker XP",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 249050,
      "has_community_visible_stats": true,
      "img_icon_url": "19f66db5192b05b71068dd243729c3d8b0d71f65",
      "name": "Dungeon of the ENDLESS™",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 251570,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "f6515dd177b2992aebcb563151fbe836a600f364",
      "name": "7 Days to Die",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 393,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 15,
      "playtime_windows_forever": 377,
      "rtime_last_played": 1731734827
    },
    {
      "appid": 261550,
      "content_descriptorids": [
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "896d5f4214e4e185a20af51b46d9dea2e6f4aaad",
      "name": "Mount & Blade II: Bannerlord",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1979,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1979,
      "rtime_last_played": 1762185573
    },
    {
      "appid": 261570,
      "has_community_visible_stats": true,
      "img_icon_url": "a8b0c1ca89fa421e5061d4ac5c17e2fbf4f08845",
      "name": "Ori and the Blind Forest",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 169,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 169,
      "rtime_last_played": 1731134997
    },
    {
      "appid": 262060,
      "has_community_visible_stats": true,
      "img_icon_url": "af219e7f9ed0506cb0954aabb7f24a45e38d28e4",
      "name": "Darkest Dungeon®",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 3410,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 3094,
      "playtime_windows_forever": 316,
      "rtime_last_played": 1752680927
    },
    {
      "appid": 281990,
      "has_community_visible_stats": true,
      "img_icon_url": "cb4a03deab1e34ed2a5cbbdf419c66bb6459625f",
      "name": "Stellaris",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 617,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 617,
      "rtime_last_played": 1744181850
    },
    {
      "appid": 282800,
      "has_community_visible_stats": true,
      "has_leaderboards": true,
      "img_icon_url": "baaf4be38deeb8a631567ee6c651ca23b65c834a",
      "name": "100% Orange Juice",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 286690,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "353ea01a045c084215bca95519808eaa7319ce0c",
      "name": "Metro 2033 Redux",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 289070,
      "has_community_visible_stats": true,
      "img_icon_url": "9dc914132fec244adcede62fb8e7524a72a7398c",
      "name": "Sid Meier's Civilization VI",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1210,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 1210,
      "playtime_windows_forever": 0,
      "rtime_last_played": 1676645121
    },
    {
      "appid": 322330,
      "img_icon_url": "a80aa6cff8eebc1cbc18c367d9ab063e1553b0ee",
      "name": "Don't Starve Together",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 1,
      "playtime_forever": 1393,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 1393,
      "playtime_windows_forever": 0,
      "rtime_last_played": 1728185602
    },
    {
      "appid": 346110,
      "has_community_visible_stats": true,
      "img_icon_url": "fef1799533131c10f538d2dd697bbbd89e663265",
      "name": "ARK: Survival Evolved",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 54,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 54,
      "rtime_last_played": 1656240646
    },
    {
      "appid": 367520,
      "has_community_visible_stats": true,
      "img_icon_url": "f6ab055c2366237200b1a31cccbd6cf81e436d72",
      "name": "Hollow Knight",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 4546,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 4119,
      "playtime_windows_forever": 427,
      "rtime_last_played": 1757058548
    },
    {
      "appid": 383180,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "68ea0c6d8ed1d089687da6318a62a7c3e3b5741b",
      "name": "Dead Island Riptide Definitive Edition",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 383270,
      "has_community_visible_stats": true,
      "img_icon_url": "48682a5e83cf7f011a15b68f460a972635742d06",
      "name": "Hue",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 387290,
      "has_community_visible_stats": true,
      "img_icon_url": "a8b0c1ca89fa421e5061d4ac5c17e2fbf4f08845",
      "name": "Ori and the Blind Forest: Definitive Edition",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 279,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 279,
      "rtime_last_played": 1756783980
    },
    {
      "appid": 391220,
      "has_community_visible_stats": true,
      "img_icon_url": "0b8a37f32ed2b7c934be8aa94d53f71e274c6497",
      "name": "Rise of the Tomb Raider",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1457,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 901,
      "playtime_windows_forever": 556,
      "rtime_last_played": 1741970444
    },
    {
      "appid": 407530,
      "img_icon_url": "807c673cddebbfee0700a947a75f4872ad136e9b",
      "name": "ARK: Survival Of The Fittest",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 2,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 2,
      "rtime_last_played": 1656230726
    },
    {
      "appid": 418670,
      "has_community_visible_stats": true,
      "has_leaderboards": true,
      "img_icon_url": "646b618afcddf400428cb3e77034be3eb1bbbf80",
      "name": "Pankapu",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 431960,
      "has_community_visible_stats": true,
      "img_icon_url": "72edaed9d748c6cf7397ffb1c83f0b837b9ebd9d",
      "name": "Wallpaper Engine",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 22,
      "playtime_forever": 5392,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 5392,
      "rtime_last_played": 1768231769
    },
    {
      "appid": 435150,
      "content_descriptorids": [
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "519a99caef7c5e2b4625c8c2fa0620fb66a752f3",
      "name": "Divinity: Original Sin 2",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 5201,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 4257,
      "playtime_windows_forever": 943,
      "rtime_last_played": 1734273680
    },
    {
      "appid": 443910,
      "img_icon_url": "0528f1a6691fcb037f9a799cda9c35f0a3a26a48",
      "name": "TGV Voyages Train Simulator",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 457140,
      "has_community_visible_stats": true,
      "img_icon_url": "d37534163ebac8351e0bda0bf30f8f2174c921b6",
      "name": "Oxygen Not Included",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 684,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 684,
      "playtime_windows_forever": 0,
      "rtime_last_played": 1708609215
    },
    {
      "appid": 460960,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "68d817a51a08c82a0afffa3008b33c38e5119ffe",
      "name": "The Deed: Dynasty",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 489520,
      "has_community_visible_stats": true,
      "img_icon_url": "ad87d123224d786a413a6021ddaf9257e26c0a28",
      "name": "Minion Masters",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 44,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 44,
      "playtime_windows_forever": 0,
      "rtime_last_played": 1673445311
    },
    {
      "appid": 489630,
      "has_community_visible_stats": true,
      "img_icon_url": "ba6ea4fbeec62073763e103450e8aa7c5373d010",
      "name": "Warhammer 40,000: Gladius - Relics of War",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 489830,
      "content_descriptorids": [
        1,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "0dfe3eed5658f9fbd8b62f8021038c0a4190f21d",
      "name": "The Elder Scrolls V: Skyrim Special Edition",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 2011,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 2011,
      "rtime_last_played": 1765373987
    },
    {
      "appid": 493540,
      "has_community_visible_stats": true,
      "img_icon_url": "2715c4d5cba6b7f5a3a4b403a9723d86d8c68ea4",
      "name": "Figment",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 544610,
      "has_community_visible_stats": true,
      "img_icon_url": "9f04e46ee137eac4bcd300c566c91c858abb3c55",
      "name": "Battlestar Galactica Deadlock",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 552500,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "a671f2ddf7359beba9702ac097baf6d50cb07202",
      "name": "Warhammer: Vermintide 2",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 582160,
      "has_community_visible_stats": true,
      "img_icon_url": "dff3a53f93d39f1e0432ec4f22d31c12aeefa36f",
      "name": "Assassin's Creed Origins",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 684,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 684,
      "rtime_last_played": 1756823061
    },
    {
      "appid": 588650,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "a431361e5dae5fd6ac2433064b62b2a37abc38f1",
      "name": "Dead Cells",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 2362,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 2362,
      "playtime_windows_forever": 0,
      "rtime_last_played": 1724428715
    },
    {
      "appid": 601150,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "7ec2f6fb9069c3ae03af7e83610862090cd757bb",
      "name": "Devil May Cry 5",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 464,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 464,
      "rtime_last_played": 1744359719
    },
    {
      "appid": 601840,
      "content_descriptorids": [
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "db635b881c25e62a67a324e66a22fde7054717c0",
      "name": "Griftlands",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 1,
      "playtime_forever": 437,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 437,
      "rtime_last_played": 1750685276
    },
    {
      "appid": 602960,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "a0adb0f29ce819c6dffa32446624fb7648defc5a",
      "name": "Barotrauma",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 196,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 119,
      "playtime_windows_forever": 77,
      "rtime_last_played": 1731138317
    },
    {
      "appid": 610570,
      "img_icon_url": "c6279c40ef6ab4e794eafd61e61be4f6f5f2f270",
      "name": "Paradox Soul",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 646570,
      "has_community_visible_stats": true,
      "has_leaderboards": true,
      "img_icon_url": "33ea124ea8c03a9ce7012d34c3b348a351612fca",
      "name": "Slay the Spire",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 132,
      "playtime_forever": 3289,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 2864,
      "playtime_windows_forever": 424,
      "rtime_last_played": 1746107451
    },
    {
      "appid": 660160,
      "has_community_visible_stats": true,
      "img_icon_url": "69e42fb6bde64f155cd5efc2f5c5a4642c18e9a4",
      "name": "Field of Glory II",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 674750,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "has_leaderboards": true,
      "img_icon_url": "fe6e2e1baee2464bd3ed030a7299f3ffb76e1a4d",
      "name": "Yet Another Zombie Defense HD",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 72,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 72,
      "rtime_last_played": 1731131015
    },
    {
      "appid": 753660,
      "has_community_visible_stats": true,
      "has_leaderboards": true,
      "img_icon_url": "0f3559c8e03858f975a1d2ab7dfb7a06a60d06de",
      "name": "AtmaSphere",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 769560,
      "has_community_visible_stats": true,
      "img_icon_url": "8ccc812dd5e5c58cf9c1009c2a3eefe12820bea5",
      "name": "Night of the Full Moon",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 373,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 373,
      "rtime_last_played": 1653922096
    },
    {
      "appid": 795100,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "a4bc5f16928232914b000ebf8f586979b6ff2cef",
      "name": "Friday the 13th: Killer Puzzle",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 43,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 43,
      "playtime_windows_forever": 0,
      "rtime_last_played": 1673878424
    },
    {
      "appid": 812140,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "4b6cf0715b30669411bf204bce7ed99a9c84671b",
      "name": "Assassin's Creed Odyssey",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 1,
      "playtime_forever": 2649,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 2649,
      "rtime_last_played": 1760010098
    },
    {
      "appid": 813540,
      "content_descriptorids": [
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "3138e1c654922fd57f59f91e6579a975aabc4ecc",
      "name": "Scheming Through The Zombie Apocalypse: The Beginning",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 877280,
      "img_icon_url": "ab16d51fcd68f9b86c1313fe1d9beb0e563afce1",
      "name": "SAO Utils 2: Progressive",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 14,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 14,
      "rtime_last_played": 1749633160
    },
    {
      "appid": 911400,
      "content_descriptorids": [
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "68e5640754e5ddf29aadff49062fa68cc8c8f4a5",
      "name": "Assassin's Creed III Remastered",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 990080,
      "has_community_visible_stats": true,
      "img_icon_url": "a9ecb94f249768d0ee5ccecbffe8d8c06d9bed59",
      "name": "Hogwarts Legacy",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 4,
      "playtime_forever": 960,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 960,
      "rtime_last_played": 1744995032
    },
    {
      "appid": 1030300,
      "has_community_visible_stats": true,
      "img_icon_url": "b4a999c1302e3ac123c041fd41bb8a34528c6ab5",
      "name": "Hollow Knight: Silksong",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 125,
      "playtime_forever": 1986,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1986,
      "rtime_last_played": 1758278620
    },
    {
      "appid": 1086940,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "d866cae7ea1e471fdbc206287111f1b642373bd9",
      "name": "Baldur's Gate 3",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 6013,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 6013,
      "rtime_last_played": 1767862020
    },
    {
      "appid": 1091500,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "42b9b33fa0f0d997beb299c6157592a8fe7d8f68",
      "name": "Cyberpunk 2077",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 22,
      "playtime_forever": 1571,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1571,
      "rtime_last_played": 1752826943
    },
    {
      "appid": 1092790,
      "has_community_visible_stats": true,
      "img_icon_url": "25c02dcbabe97febe787797195099325a4d47935",
      "name": "Inscryption",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 498,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 498,
      "rtime_last_played": 1732548168
    },
    {
      "appid": 1134700,
      "has_community_visible_stats": true,
      "img_icon_url": "8594527d19edbfdb2ded666dd09573f4542c282f",
      "name": "Wild Terra 2: New Lands",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 1144770,
      "content_descriptorids": [
        1,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "cd91eebd4b1f4064f460769fd8477fb7a6a2bffa",
      "name": "SLUDGE LIFE",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 1145360,
      "has_community_visible_stats": true,
      "img_icon_url": "8a3fca36a00883e8066263ad35dd15d77a1f9abc",
      "name": "Hades",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 2757,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 2757,
      "playtime_windows_forever": 0,
      "rtime_last_played": 1708179617
    },
    {
      "appid": 1174180,
      "content_descriptorids": [
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "5106abd9c1187a97f23295a0ba9470c94804ec6c",
      "name": "Red Dead Redemption 2",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 537,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 537,
      "rtime_last_played": 1754816084
    },
    {
      "appid": 1189490,
      "has_community_visible_stats": true,
      "img_icon_url": "f242f2631b18b9644781ba1df9af65ae18e59bf9",
      "name": "觅长生",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1578,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1578,
      "rtime_last_played": 1758464019
    },
    {
      "appid": 1200580,
      "has_community_visible_stats": true,
      "img_icon_url": "112744df8d62d560790e3bc3a64fb0d745bde331",
      "name": "One Gun Guy",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 1216710,
      "has_community_visible_stats": true,
      "img_icon_url": "7a65b4ed6f62464394e32192a7a43b218879b21f",
      "name": "Cyber Manhunt",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 431,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 431,
      "rtime_last_played": 1750651694
    },
    {
      "appid": 1245620,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "b6e290dd5a92ce98f89089a207733c70c41a1871",
      "name": "ELDEN RING",
      "playtime_2weeks": 148,
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 6306,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 6306,
      "rtime_last_played": 1769143692
    },
    {
      "appid": 1281930,
      "img_icon_url": "e8a125078a31b8475994e8ce4d8d6fdd6becc131",
      "name": "tModLoader",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 170,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 170,
      "rtime_last_played": 1744544265
    },
    {
      "appid": 1340990,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "27e73dd43a02f2703f507f0022adf36de4d45590",
      "name": "Rise of the Ronin",
      "playtime_2weeks": 254,
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1579,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1579,
      "rtime_last_played": 1769158273
    },
    {
      "appid": 1371980,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "img_icon_url": "8b383999493fa60adbbda2a5a5714805d9d7c913",
      "name": "No Rest for the Wicked",
      "playtime_2weeks": 1328,
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1328,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1328,
      "rtime_last_played": 1769594792
    },
    {
      "appid": 1608450,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "733a62d2f790189f9cecb01bebf8e014a231a86e",
      "name": "Hellslave",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 0,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 0,
      "rtime_last_played": 0
    },
    {
      "appid": 1684350,
      "content_descriptorids": [
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "cbe9185d27a6b35a2f0c913a4eb49da15c937a3f",
      "name": "The Thaumaturge",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 353,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 353,
      "rtime_last_played": 1748693982
    },
    {
      "appid": 1687950,
      "content_descriptorids": [
        1,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "2f868d8c16fc357dc7122d440b9de3916e36e6fa",
      "name": "Persona 5 Royal",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1850,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1850,
      "rtime_last_played": 1750261727
    },
    {
      "appid": 1771300,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "80e8d75b87433627cafd2a1bcbb5b9f5741e2277",
      "name": "Kingdom Come: Deliverance II",
      "playtime_2weeks": 364,
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 2981,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 2981,
      "rtime_last_played": 1768905285
    },
    {
      "appid": 1876890,
      "has_community_visible_stats": true,
      "img_icon_url": "a84d2eb117aa4d7f32781b5020f9e90d567da183",
      "name": "Wandering Sword",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1651,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1651,
      "rtime_last_played": 1759653720
    },
    {
      "appid": 1903340,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "d48fb3ed033a08bad9bf0a2e1ceb145e58ffe0aa",
      "name": "Clair Obscur: Expedition 33",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1291,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1291,
      "rtime_last_played": 1767251363
    },
    {
      "appid": 1942280,
      "has_community_visible_stats": true,
      "img_icon_url": "d9dfcab8f300a9548439f70bef7b5f4e53d0fc28",
      "name": "Brotato",
      "playtime_2weeks": 53,
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 477,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 477,
      "rtime_last_played": 1769147287
    },
    {
      "appid": 1948800,
      "has_community_visible_stats": true,
      "img_icon_url": "c3c282d3a672cecfb9d78fc73702e2eed1441f4e",
      "name": "Yi Xian: The Cultivation Card Game",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 682,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 682,
      "playtime_windows_forever": 0,
      "rtime_last_played": 1709655242
    },
    {
      "appid": 2001120,
      "has_community_visible_stats": true,
      "img_icon_url": "a01dc6ea47db8c74964d581fe9f1f8039e0e4f33",
      "name": "Split Fiction",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 464,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 464,
      "rtime_last_played": 1754828850
    },
    {
      "appid": 2050650,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "817358b8013c55831ea10d031ef9c0b151110826",
      "name": "Resident Evil 4",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 1,
      "playtime_forever": 433,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 433,
      "rtime_last_played": 1756563312
    },
    {
      "appid": 2208920,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "3946f91cf6beb0d384a85fc32d71616313dc362e",
      "name": "Assassin's Creed Valhalla",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 111,
      "playtime_forever": 1313,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1313,
      "rtime_last_played": 1759566609
    },
    {
      "appid": 2215430,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "e87b8cbe31f7bc5f40ee6ed94ccfa18f59f04fbc",
      "name": "Ghost of Tsushima DIRECTOR'S CUT",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1974,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1974,
      "rtime_last_played": 1760539212
    },
    {
      "appid": 2277560,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "06a62ea3a0cb8c177a0e336696d174ceacd003f4",
      "name": "WUCHANG: Fallen Feathers",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 156,
      "playtime_forever": 1411,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1411,
      "rtime_last_played": 1755614794
    },
    {
      "appid": 2358720,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "764ad8ff458f7020d63a3f7f0abf6ad8882c05df",
      "name": "Black Myth: Wukong",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 2110,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 2110,
      "rtime_last_played": 1749115336
    },
    {
      "appid": 2379780,
      "has_community_visible_stats": true,
      "img_icon_url": "b6018068070ab0e23561694c11f7950dd6f4c752",
      "name": "Balatro",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 1,
      "playtime_forever": 616,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 616,
      "rtime_last_played": 1750662263
    },
    {
      "appid": 3117820,
      "content_descriptorids": [
        1,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "81e37cf744f52d7af999e208dfd4c087a1f3db29",
      "name": "Sultan's Game",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 718,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 718,
      "rtime_last_played": 1749116205
    },
    {
      "appid": 3159330,
      "content_descriptorids": [
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "1f8f5a64b174f9cc07d5b277e7b08219c262511f",
      "name": "Assassin's Creed Shadows",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 63,
      "playtime_forever": 2279,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 2279,
      "rtime_last_played": 1765457827
    },
    {
      "appid": 3167020,
      "has_community_visible_stats": true,
      "img_icon_url": "5bb8d31708442a8f3ddbc100d7be7c3fde530d18",
      "name": "Escape From Duckov",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 5,
      "playtime_forever": 1398,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1398,
      "rtime_last_played": 1761813283
    },
    {
      "appid": 3489700,
      "content_descriptorids": [
        1,
        2,
        5
      ],
      "has_community_visible_stats": true,
      "img_icon_url": "57038a59c95ccee823169ffd580adef713543d46",
      "name": "Stellar Blade™",
      "playtime_deck_forever": 0,
      "playtime_disconnected": 0,
      "playtime_forever": 1643,
      "playtime_linux_forever": 0,
      "playtime_mac_forever": 0,
      "playtime_windows_forever": 1643,
      "rtime_last_played": 1750148107
    }
  ]
}

================================================================================
ISteamUserStats.GetSchemaForGame
--------------------------------------------------------------------------------
{
  "game": {
    "availableGameStats": {
      "achievements": [
        {
          "defaultvalue": 0,
          "displayName": "This is Sparta!",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/08bdee6fbec196b65f29410ea6f010c867b59831.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/2f0632ae479d3e8f7c54334e3712644737f2ec91.jpg",
          "name": "001"
        },
        {
          "defaultvalue": 0,
          "displayName": "An Odyssey in the Making",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c58f97403e0af4b9499ed050a4feba0aa0f735ed.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/38d681656d762f3a6843dd17be22dbc4c22a5d92.jpg",
          "name": "002"
        },
        {
          "defaultvalue": 0,
          "displayName": "Past Mistakes",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/8e2a784eadfac62a89ae808c18466f49deb619f1.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6725f07920fff23a1ff6f2b1c0138258931f31e1.jpg",
          "name": "003"
        },
        {
          "defaultvalue": 0,
          "displayName": "Evil Unearthed",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/60ff1d190e02613f4a54b5192ab9a0485e5d61d6.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/56d3c7c9e8002be9540db241edf124b6a0bb2815.jpg",
          "name": "004"
        },
        {
          "defaultvalue": 0,
          "displayName": "The Bright Minds",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/7c2c1b40626a49c02744dd6ca60a845c3f0301aa.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b0764531472f3a16f1f0d3119ab201f39ea64367.jpg",
          "name": "005"
        },
        {
          "defaultvalue": 0,
          "displayName": "From the Ashes",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/55fe4a7f901249547f42eeead46c6d6af2017ee1.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/2001e47fffdec18d51e2fad40e53bbab08fd068b.jpg",
          "name": "006"
        },
        {
          "defaultvalue": 0,
          "displayName": "Democracy Falls",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9a47412ae5495838d4237bf9ae7a7277f9d5fb06.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/5c6213b564494c578ffea174bb9ae7499474db3d.jpg",
          "name": "007"
        },
        {
          "defaultvalue": 0,
          "displayName": "Legend in the Making",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/ab2bd901b6a1ca19f9b3392e66222276effaa0a7.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/3df83373f0c5dce5c37e5506a9339f6ea4324cfc.jpg",
          "name": "008"
        },
        {
          "defaultvalue": 0,
          "displayName": "Taking Back Athens",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/4149eeda5f9fcbf6e508ec65d5b34a2f81cf3d6b.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/fba5eed7d7b4eeb8efce9591d11e75069bf63d81.jpg",
          "name": "009"
        },
        {
          "defaultvalue": 0,
          "displayName": "Odyssey's End",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/d338a222e00dcb456eb6d9d94f3bda859b2a821d.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/253e267b567331d4645993d1c3aace627b7d0221.jpg",
          "name": "010"
        },
        {
          "defaultvalue": 0,
          "description": "Complete all underwater location objectives.",
          "displayName": "Child of Poseidon",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/ccc98eec9c6529bd33440b9303e98448175e67ed.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/8525c9861e332d62f45510421148107638d53380.jpg",
          "name": "011"
        },
        {
          "defaultvalue": 0,
          "description": "Engrave your first item.",
          "displayName": "Make It Your Own",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/78af3993c76ad41e07295891e566c26ab9cc9409.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/7fe16966201ab3e7745c7c828aced2ce026c2551.jpg",
          "name": "012"
        },
        {
          "defaultvalue": 0,
          "description": "Recruit and assign a Legendary NPC for your ship.",
          "displayName": "You Work for Me Now",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6f7ed0b89648438f12519277c6e44063d4395795.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/5057916f2d0df964bd5aed51b13017f649a68ea9.jpg",
          "name": "013"
        },
        {
          "defaultvalue": 0,
          "description": "Acquire and equip your first Legendary item.",
          "displayName": "Shiny!",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/022b72b7d990c78f6bb8d47df5e00de31b27b7c6.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9c5923c3a2048642a590670fab99405952c1db42.jpg",
          "name": "014"
        },
        {
          "defaultvalue": 0,
          "description": "Equip 1 Legendary melee weapon and 5 Legendary armor pieces.",
          "displayName": "I am Legend",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/5c5e5c50a3783a63329daad9007c2a2283fd8c19.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/25b797ace6ae14827f8a0dcba33d5e269adf171a.jpg",
          "name": "015"
        },
        {
          "defaultvalue": 0,
          "description": "Become Champion of the Arena.",
          "displayName": "Are You Not Entertained?",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/0a1d8d8735a89c1ef1258eed64bca31f2b491264.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/5cb6de08bb07cd48f0ebe13815fda9b1db3a4164.jpg",
          "name": "016"
        },
        {
          "defaultvalue": 0,
          "description": "Reach Level 50.",
          "displayName": "Demigod",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/d67cdae71b6bf5dfe501825f0be012712c86247d.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/19e66d2a919142539a8e5966ebe7a78387dc67f4.jpg",
          "name": "017"
        },
        {
          "defaultvalue": 0,
          "description": "Acquire a Tier 3 active Ability.",
          "displayName": "Godly Power",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/2ea21bcd712d3a0434e48d80f928f1f8268eee0b.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/045dc9836d8df137eff48a535d7ec6286dc8abb7.jpg",
          "name": "018"
        },
        {
          "defaultvalue": 0,
          "displayName": "Legacy Restored",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/ccca15a9a1c8655f11ff349f6d693cf1f272a1f2.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/3f8946d38d9e66eed8aaa9ba00605e8731dd634e.jpg",
          "name": "019"
        },
        {
          "defaultvalue": 0,
          "description": "Become the first Mercenary.",
          "displayName": "Top of the Food Chain",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f3164494ed05aee2423106bf061f922fb67660e6.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/928bc39f3a31c507ccc4660f2310a51003bbd760.jpg",
          "name": "020"
        },
        {
          "defaultvalue": 0,
          "displayName": "The Cult Unmasked",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/cc619ac9660c750e0ccd53bc7407f8a81d616f82.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/18cee0eff66ae09549d3771b5bec763da58eb261.jpg",
          "name": "021"
        },
        {
          "defaultvalue": 0,
          "displayName": "Stink Eye",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/8a08b72562dc697f79e681984fe62f7b47ba05eb.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/bcdfaef80b871d9f05e82affff84bac59576fa2d.jpg",
          "name": "022"
        },
        {
          "defaultvalue": 0,
          "description": "Unveil all sub-regions of Greece.",
          "displayName": "Hermes's Homie",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6176ce209f324f8d84059a11e073ac893902f45b.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/51b83845ebd352e0cf327f00268abc1b67ae9137.jpg",
          "name": "023"
        },
        {
          "defaultvalue": 0,
          "displayName": "In Perseus's Image",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/2df5930767f347daee02a886e869a8f457184eb0.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/30ae0b436313cf59138016113e7da69b02601184.jpg",
          "name": "024"
        },
        {
          "defaultvalue": 0,
          "displayName": "A-maze-ing Victory!",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/11c6c5dc829ed8dbcbbf2a14508d7a14fe0113ac.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9198c4e3c2a6077fdcbab2de4512c79cb2c0fda1.jpg",
          "name": "025"
        },
        {
          "defaultvalue": 0,
          "displayName": "Eye on the Prize",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/eb9029ded7346b44c478af07b2a4dd46f79ab9d1.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/296734ab9de033dfcecb3b2b7015b9fb5af9f498.jpg",
          "name": "026"
        },
        {
          "defaultvalue": 0,
          "displayName": "Riddle Me This",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b8d6fc8988fcfce8ffa4c1d0ac921db70f93bfab.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6ff8ce254a182d1006efb23d317599ddc0a3c159.jpg",
          "name": "027"
        },
        {
          "defaultvalue": 0,
          "description": "Upgrade the Adrestia to Legendary Status.",
          "displayName": "Lord of the Seas",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/0ce3a2a20b18f68e1ffa8d5b727ad056fadf0858.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f7a3cacda386863abee274532144c1c033551406.jpg",
          "name": "028"
        },
        {
          "defaultvalue": 0,
          "description": "Fully crew the Adrestia with Legendary Lieutenants.",
          "displayName": "The Argonauts",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/4db379c844901bd89c54d79ba003d4a824e3ae09.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/1124bc5bf85685c6352e7abf2152d9f749ebcfae.jpg",
          "name": "029"
        },
        {
          "defaultvalue": 0,
          "displayName": "Master of the Hunt",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6226f64a39255371a16d244e02246efd7c17adae.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6bf17bad1520340ae210267b4180ad3a6642fd05.jpg",
          "name": "030"
        },
        {
          "defaultvalue": 0,
          "displayName": "Everybody Benefits",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/12ca9eb31bf254dfb2adc66c717ca7f862578088.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b668fc86672023f6838503465580f7afdc3c29ff.jpg",
          "name": "031"
        },
        {
          "defaultvalue": 0,
          "displayName": "Trust Me, I'm a Doctor",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/abb007f70efd6a6546f3bcd73cbef6b3b2a5db07.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f99029f770fc7ec0ae0a17a36c85d9415dd85a8a.jpg",
          "name": "032"
        },
        {
          "defaultvalue": 0,
          "displayName": "A Pirate's Life for Me",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c1c9c29964e18a3ed687aef9360583d71982611c.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/76d2c7289ead317f3775a23c331ba0a90ae7708d.jpg",
          "name": "033"
        },
        {
          "defaultvalue": 0,
          "displayName": "Going For Gold",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9c3f103532a7868a66e2b4cc41f55ebd7ed8adf9.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/efddf4cbdab38f05c921d5cc8ee56cb67af6e214.jpg",
          "name": "034"
        },
        {
          "defaultvalue": 0,
          "description": "Sink your first Epic Ship.",
          "displayName": "Scourge of the Aegean",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/91692849c59e4e9d17573effa26142711b3a8b44.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/1840ffe1879e61409a9690d591d09d322b07ccb8.jpg",
          "name": "035"
        },
        {
          "defaultvalue": 0,
          "description": "Defeat a Mercenary in the Arena.",
          "displayName": "Blood Sport",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/503aab5fc61aeed9b18b29407a75435c35064e1f.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/97402dc7ac74e0b4389856c47d013087f6b6fbdc.jpg",
          "name": "036"
        },
        {
          "defaultvalue": 0,
          "description": "Upgrade the Adrestia for the first time.",
          "displayName": "Harder, Better, Faster, Stronger",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/64504d3bf8e96402090be580b39b325a72062ad2.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/a6447070a3320a13b3f5cc460e1525f2709986e3.jpg",
          "name": "037"
        },
        {
          "defaultvalue": 0,
          "description": "Equip a Legendary Armor set.",
          "displayName": "Fashion's Creed",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/89978ce9744577143659811ebfdc155105d0ba85.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/d4d1923c18290896014ec65b6aa97f65212707df.jpg",
          "name": "038"
        },
        {
          "defaultvalue": 0,
          "description": "Spend the night with another character.",
          "displayName": "Aphrodite's Embrace",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/ecf8966eefe2db4f36d16bc3d0388f80426f8f21.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/7aaf05b9593c92cc3cb54b0a16ef425a9b13ed14.jpg",
          "name": "039"
        },
        {
          "defaultvalue": 0,
          "displayName": "One Head Down…",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b874d44d8d5110a27c6cb9395b76fa359f077008.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/7cdda8a3b12d33f4a6ccb428f4c0a98e6aca180f.jpg",
          "name": "040"
        },
        {
          "defaultvalue": 0,
          "displayName": "Birthright",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/8ec2ee7f6150bb5682349c93af1b4a23f46f3d01.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/38d84d6ac45ca048ff510cf2cc88be2909fd65c7.jpg",
          "name": "041"
        },
        {
          "defaultvalue": 0,
          "description": "Cleave a ship in half.",
          "displayName": "Ramming Speed",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/1efb366674f2bf2e21feb0946d200859f3b35e86.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/7b1d6bbe66cac0d502bbeb0494791c849873ce07.jpg",
          "name": "042"
        },
        {
          "defaultvalue": 0,
          "description": "Perform an Overpower Attack with every weapon type.",
          "displayName": "I Have the Power",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c76f77b46a39fdf1c0ff6b011f83ed3a57a3c049.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/7a88e742d00683c2a8c7881a5786de7e401e7d0c.jpg",
          "name": "043"
        },
        {
          "defaultvalue": 0,
          "description": "Kill the Leader of any Region with Low Resources, other than Megaris.",
          "displayName": "War Master",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/50772b9e8445f0a6e4087844f8f6d0482927e954.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/02d852b464b2e34974ca6af3debc9277234bc152.jpg",
          "name": "044"
        },
        {
          "defaultvalue": 0,
          "description": "Complete 20 Bounties, War Contracts, or Naval Quests from Message Boards.",
          "displayName": "Misthios in Training",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/8d127df60af14cef251ea1652701aa07a323a4fa.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f93d4ebab6ec0452aa90f7f8ef5dfe810ab0965b.jpg",
          "name": "045"
        },
        {
          "defaultvalue": 0,
          "description": "Complete 20 Quests on Pephka, Obsidian and Abantis islands.",
          "displayName": "Island Hopper",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9f8b64b530e39dfb92117fbdc40ad1289a118429.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/699f43a0ee2c5d2661b81f294b4ceb59342460d7.jpg",
          "name": "046"
        },
        {
          "defaultvalue": 0,
          "description": "Raise your Bounty to the maximum level.",
          "displayName": "Infamous",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/12eb5190c1578ef305a5996a283bfc3e400c38bc.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/da4273e6a2acf32c3ec0e74d97d7fdfa2c1341dc.jpg",
          "name": "047"
        },
        {
          "defaultvalue": 0,
          "description": "Win your first on land conquest battle in any region (excluding Megaris in Hero's Journey).",
          "displayName": "Hero for Hire",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/19501757c3e3699086dd4e819b17c469c4c443c1.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b0100235969f16bfd78cb6d0f1cb7581b1dedf6c.jpg",
          "name": "048"
        },
        {
          "defaultvalue": 0,
          "displayName": "Wrath of the Amazons",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b6f327fb43540921a7b79a394f063b0e4e6b2a28.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/3c6e4e94bf7132ed89327b7013427cb6f7b3cc99.jpg",
          "name": "049"
        },
        {
          "defaultvalue": 0,
          "description": "Engrave a Legendary Item with a Legendary Effect.",
          "displayName": "The Midas Touch",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/99a5100a8c20faa6c106b0d8b0ae0bd80ae2d9a8.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c882bd680f66799bfaa47ae4da5062efb88c7072.jpg",
          "name": "050"
        },
        {
          "defaultvalue": 0,
          "description": "Complete The Show Must Go On.",
          "displayName": "The Show Must Go On",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/ba431007ef8e18e6a5fb3f7721cce95d59f2fb0e.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/3cda836a03b3a91b348c2816f051ed0580d1ec77.jpg",
          "name": "051"
        },
        {
          "defaultvalue": 0,
          "description": "Defeat Steropes the Lightning Bringer.",
          "displayName": "Lightning Rod",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f5e662bd1a7901719af9e4e06938c44719957839.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/a6f6186407e572cefcd5b8d28c1d1ce8027cd225.jpg",
          "name": "052"
        },
        {
          "defaultvalue": 0,
          "description": "Complete Divine Intervention.",
          "displayName": "Divine Intervention",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/e202c1c82a568115c9aa1fe32c9129ee8cd6babe.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9b157970efc964062b4d59527a7ec8f888a53ef1.jpg",
          "name": "053"
        },
        {
          "defaultvalue": 0,
          "description": "Defeat Arges, the Bright One",
          "displayName": "Volcanic Sunscreen",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/1da03f12cf661ec9023f7daf327d79ea2092b6b3.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/0f80f4dfd32dd338c752a5e693741e534bc9b0f4.jpg",
          "name": "054"
        },
        {
          "defaultvalue": 0,
          "description": "Complete The Image of Faith",
          "displayName": "The Image of Faith",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/4ba9a4b176f93cbaf4fc118342a3787da0c983d1.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/cb38e93949ac0e63f28fcff663106706bbb2bf4b.jpg",
          "name": "055"
        },
        {
          "defaultvalue": 0,
          "description": "Complete The Daughters of Lalaia",
          "displayName": "The Daughters of Lalaia",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/0c7e997edf455b8c791cad3e3dfb662e85542b0b.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b46edc3368d164d8868ef01eaab01023d0a0cb69.jpg",
          "name": "056"
        },
        {
          "defaultvalue": 0,
          "description": "Kill the Makedonian Lion",
          "displayName": "Lone Lion",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/36e6a7339dc5dd55da8ed56c4b99dc7ee397e3e5.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/411d954c441a83ca4506558e429dc2ad433c4baf.jpg",
          "name": "064"
        },
        {
          "defaultvalue": 0,
          "description": "Kill 10 enemies using the Death Veil ability",
          "displayName": "Without a trace",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/26d652d16c115377cf5462ea82c33b8114e9b0fe.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f914958587b3eef2252c977b6614d60d3fadfb2d.jpg",
          "name": "065"
        },
        {
          "defaultvalue": 0,
          "displayName": "The Start of a Legacy",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/d03b4a3c71197ce288905aded474c04d193b8cc7.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b5513f05b8b3156e505e322ec13d43a2a350218a.jpg",
          "name": "066"
        },
        {
          "defaultvalue": 0,
          "description": "Land a Rush Assassinate that chains 4 times with the Blade of the Lion",
          "displayName": "Breaking the Limit",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9013a7cfdf7e36bbe10a22e646455428c6dbf850.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c3d5f1aad370a46a29e00cf19f74dbb3864246c6.jpg",
          "name": "067"
        },
        {
          "defaultvalue": 0,
          "description": "Kill all the Ancients in the Order of the Hunters in Makedonia",
          "displayName": "Predator and Prey",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/a4c54de720cfd99578200c475d479d02c5a36867.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/3ca56b69c572051de41ddf6747c5fa0bef8abb72.jpg",
          "name": "068"
        },
        {
          "defaultvalue": 0,
          "description": "Complete A Poet's Legacy.",
          "displayName": "A Poet's Legacy",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/ead3e8ff8b22eb7d5345b14d70f6d47fc15b3b8b.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/e810b0f9709970e55803c101d8a56ba6d8d42e6e.jpg",
          "name": "057"
        },
        {
          "defaultvalue": 0,
          "description": "Complete A Brother's Seduction",
          "displayName": "A Brother's Seduction",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c88fdd1e2579ad45e13f13739e80852356bf3b82.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/d29eadba4b82420e1e1dddf82a74cbba891f891e.jpg",
          "name": "058"
        },
        {
          "defaultvalue": 0,
          "description": "Kill 10 enemies using the Rapid Fire ability.",
          "displayName": "Rain of Arrows",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/965401595d92e3680d7f3dc4acd2572ac2d67ff3.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/1acb0fb715f7ebd61b2ff7320e710e7478fa6ab9.jpg",
          "name": "069"
        },
        {
          "defaultvalue": 0,
          "description": "Set 10 enemy ships on fire.",
          "displayName": "Fire on Water",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/7e303a26e83446af80b191e2b571e6d077dd1d12.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/4502d944bb8e9f6bad4e9c36ea6c3b66b3f91569.jpg",
          "name": "070"
        },
        {
          "defaultvalue": 0,
          "description": "Heal by parrying 10 times with the Judgment of the Lion.",
          "displayName": "Parry to Carry",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c45ae1e8aed554fe3e3dc33b44fd849bb6fb9bed.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/19c685e15cd4660266cca2e2aca9c4f77a3ff5cb.jpg",
          "name": "071"
        },
        {
          "defaultvalue": 0,
          "displayName": "Blood of Leonidas",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b42a1d3745eee1f1e9b82cb23a31c3f045893213.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/fed703f3031d5d8bc1374fa619bd21d766ae94e1.jpg",
          "name": "072"
        },
        {
          "defaultvalue": 0,
          "description": "Kill all of the Ancients in the Order of the Storm in Achaia.",
          "displayName": "Stormculler",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/924e8bd334ef61b0818fbadad8afde697f47dbcc.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/14b2f02ec533d280bff026a2626740463624f490.jpg",
          "name": "073"
        },
        {
          "defaultvalue": 0,
          "description": "Complete A Friend Worth Dying For",
          "displayName": "A Friend Worth Dying For",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6227d0416d1c294044296f0d713547f57b296f11.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/488375cef96a0ab63b0065bcf2342804d9660956.jpg",
          "name": "059"
        },
        {
          "defaultvalue": 0,
          "description": "Complete The Heir of Memories",
          "displayName": "The Heir of Memories",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/cb99e8bdd22aa6302bc2bec7df222bca355b8a6a.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/142bc64d2d9bc5c5811c1fa90681a569e5185902.jpg",
          "name": "060"
        },
        {
          "defaultvalue": 0,
          "description": "Kill 10 enemies using the Fury of the Bloodline Ability.",
          "displayName": "Seeing Red",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/7efdd55e2d7eb5cf43b6408da6d076edd49183c2.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/355bf3be6b401856b967fab9b40a7aa9f3ae65dd.jpg",
          "name": "074"
        },
        {
          "defaultvalue": 0,
          "displayName": "Bittersweet Beginnings",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6ee6edea64593bc697b0e0c2bae79a61129868e0.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f31f74a2bddd8a4e65c4840cd82958ff5e789bbb.jpg",
          "name": "075"
        },
        {
          "defaultvalue": 0,
          "description": "Heal by getting 10 headshot kills while you have the Golden Harbinger equipped.",
          "displayName": "Surgical Sniper",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c56495dd3802692cbae5101dc8e95f6df7d428c7.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/e11d65b8cf8bf5045c4c3c32b5aa448b7eae5739.jpg",
          "name": "076"
        },
        {
          "defaultvalue": 0,
          "description": "Acquire the Sword of Kings",
          "displayName": "Kingmaker",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/2191610e732c38259362776666bfbbed98161b50.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/eedb293be81151b24ca7a83e074f1ce85a366b75.jpg",
          "name": "077"
        },
        {
          "defaultvalue": 0,
          "description": "Kill all the Ancients in the Order of Dominion in Messenia",
          "displayName": "For Love of Persia",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/fa09b0a57cca75a7c82bfa629b3045fe82983261.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/a6399eab4c62dcbfb8242569e067e297134f2d61.jpg",
          "name": "078"
        },
        {
          "defaultvalue": 0,
          "description": "Complete One Really, Really Bad Day",
          "displayName": "One Really, Really Bad Day",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f0ca07ecfcf5c055cd5f5066890eac20159485af.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/80a43e5e6b0e7b6b75f8a937b6731a81089eda63.jpg",
          "name": "061"
        },
        {
          "defaultvalue": 0,
          "description": "Complete Every Story Has an Ending",
          "displayName": "Every Story Has an Ending",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/2a5c89bd79773f088dc53faef91afa84093138e9.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/17278d156cd8b2fb51f6cc3bae09e619c0ae8024.jpg",
          "name": "062"
        },
        {
          "defaultvalue": 0,
          "description": "Kill all Overseers in Elysium.",
          "displayName": "No More Rulers",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9cd51d91ba11c04c6219de53bdeb16df9fa61778.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/4090ee330f6411dfcfc065701990fb879f6898ce.jpg",
          "name": "079"
        },
        {
          "defaultvalue": 0,
          "displayName": "In the Face of the Gods",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/e433e46d669bd080c90b8f401c3205fe301e8d9c.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/94025242974ce0163cb61e3797b30cf1e51a334f.jpg",
          "name": "080"
        },
        {
          "defaultvalue": 0,
          "description": "Destroy all of the Marble Maiden Tributes.",
          "displayName": "Blasphemer",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/f0111bf81007539e1a5bccc9e3f4f10d2534af78.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/679462e9492098ac02dce5116476e4f7a23a46bc.jpg",
          "name": "081"
        },
        {
          "defaultvalue": 0,
          "description": "Collect all the Keeper's Insights in Episode 1.",
          "displayName": "Gathering Strength",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/bd495c61b99f06648e3ad17f33a03735c78b6609.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/778c666a23efcb694f8678d63dd50eee1e7da695.jpg",
          "name": "082"
        },
        {
          "defaultvalue": 0,
          "description": "Win the conquest of Elysium with freed humans from the 3 main regions.",
          "displayName": "The Conqueror",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/1ba21c7195b655c8f473a8501a6c6af7c89568d2.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/756f97709f07ebc45f715d397ebf2a7ab3f05aa8.jpg",
          "name": "083"
        },
        {
          "defaultvalue": 0,
          "description": "Complete Old Flames Burn Brighter",
          "displayName": "Old Flames Burn Brighter",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/1fda325db9c5c7fba8e801f9c744b546b2f782f2.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c1e40393242a8e1d882107bba1d53f55ef01033d.jpg",
          "name": "063"
        },
        {
          "defaultvalue": 0,
          "description": "Defeat Cerberos.",
          "displayName": "Bad Dog!",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/6233dc7a35a251afdc406d3f383f8ccb6edfcdcf.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9cf077d11a9c0880d4e4f231e652cad33c34d4ce.jpg",
          "name": "084"
        },
        {
          "defaultvalue": 0,
          "description": "Close all Tartaros Rifts.",
          "displayName": "Guardian of the Underworld",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/0572e62b27b982bd82efa2782daab085ead338eb.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/3868eda2cfe93a3a1a590dba787862d4d6c01761.jpg",
          "name": "085"
        },
        {
          "defaultvalue": 0,
          "description": "Defeat all of the Fallen.",
          "displayName": "The One",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/2364804e7ef25ec46883ffb1206df1fff8f0d398.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/b7f9f81fbc0de909855ec063f1fe1a32a2bd3e83.jpg",
          "name": "086"
        },
        {
          "defaultvalue": 0,
          "description": "Collect all the Keeper's Insights in Episode 2.",
          "displayName": "Gathering More Strength",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/9478a26b9078407777916294851b88cdc8a05721.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/686e587c8759a012f33bb480d5932ef2ea1795fb.jpg",
          "name": "087"
        },
        {
          "defaultvalue": 0,
          "displayName": "A True Ruler",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/8399797d1aa32de00cc05dd9fa94ca16630a5406.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/ccec810c09cecca133f44660c42935c2b32d9737.jpg",
          "name": "088"
        },
        {
          "defaultvalue": 0,
          "description": "Kill 10 Isu Soldiers with the Blessing of Kronos enhancement.",
          "displayName": "Your Own Medicine",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/3150528999a5ab2a8dfc7b2d97a547ab88505b6b.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/ca689af92501616e805771ccdbe634a68368d859.jpg",
          "name": "089"
        },
        {
          "defaultvalue": 0,
          "description": "Completely fill the Knowledge Sequence.",
          "displayName": "Isu Bloodline",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/4199853c7d8ccd400bc56f8f7e5043ba806cfc24.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/2bf84c01b0b976b1c1c32a60a07416b4b29dd62b.jpg",
          "name": "090"
        },
        {
          "defaultvalue": 0,
          "description": "Forge the 3 Legendary Weapons.",
          "displayName": "Hephaistos's Apprentice",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/c714ee98e1d2b67c1580d0ee955c71e3bc85232e.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/376e50a3f4b16efc2e5fb6097d70cbbc4717dcc6.jpg",
          "name": "091"
        },
        {
          "defaultvalue": 0,
          "description": "Collect all the Keeper's Insights in Episode 3.",
          "displayName": "Gathering Full Strength",
          "hidden": 0,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/3ebd4b53b729996f4c0e138b9fb2af9e68a0b10e.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/537a7cf49e95a855d2c49c0f684dd94fc6e95d36.jpg",
          "name": "092"
        },
        {
          "defaultvalue": 0,
          "displayName": "1 Versus 100",
          "hidden": 1,
          "icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/74fe04106e7e876bb9c3b4fc386906bce1de5a4e.jpg",
          "icongray": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/812140/666d15b7c1220dd37093848c58ea10fd4e832261.jpg",
          "name": "093"
        }
      ]
    },
    "gameName": "Assassin's Creed Odyssey",
    "gameVersion": "21"
  }
}

================================================================================
ISteamUserStats.GetGlobalAchievementPercentagesForApp
--------------------------------------------------------------------------------
{
  "achievementpercentages": {
    "achievements": [
      {
        "name": "001",
        "percent": "91.3"
      },
      {
        "name": "014",
        "percent": "83.3"
      },
      {
        "name": "015",
        "percent": "74.4"
      },
      {
        "name": "038",
        "percent": "70.7"
      },
      {
        "name": "002",
        "percent": "70.7"
      },
      {
        "name": "003",
        "percent": "64.8"
      },
      {
        "name": "037",
        "percent": "63.4"
      },
      {
        "name": "042",
        "percent": "62.7"
      },
      {
        "name": "013",
        "percent": "62.4"
      },
      {
        "name": "012",
        "percent": "61.0"
      },
      {
        "name": "004",
        "percent": "59.2"
      },
      {
        "name": "039",
        "percent": "57.8"
      },
      {
        "name": "035",
        "percent": "53.7"
      },
      {
        "name": "048",
        "percent": "51.9"
      },
      {
        "name": "005",
        "percent": "50.2"
      },
      {
        "name": "044",
        "percent": "49.1"
      },
      {
        "name": "006",
        "percent": "42.5"
      },
      {
        "name": "050",
        "percent": "42.3"
      },
      {
        "name": "007",
        "percent": "42.0"
      },
      {
        "name": "047",
        "percent": "40.6"
      },
      {
        "name": "040",
        "percent": "37.7"
      },
      {
        "name": "018",
        "percent": "36.9"
      },
      {
        "name": "041",
        "percent": "36.3"
      },
      {
        "name": "034",
        "percent": "35.2"
      },
      {
        "name": "029",
        "percent": "35.0"
      },
      {
        "name": "008",
        "percent": "33.6"
      },
      {
        "name": "036",
        "percent": "33.2"
      },
      {
        "name": "027",
        "percent": "32.8"
      },
      {
        "name": "009",
        "percent": "32.7"
      },
      {
        "name": "010",
        "percent": "32.4"
      },
      {
        "name": "017",
        "percent": "31.9"
      },
      {
        "name": "025",
        "percent": "31.8"
      },
      {
        "name": "049",
        "percent": "30.5"
      },
      {
        "name": "026",
        "percent": "30.4"
      },
      {
        "name": "052",
        "percent": "30.3"
      },
      {
        "name": "016",
        "percent": "29.9"
      },
      {
        "name": "020",
        "percent": "29.1"
      },
      {
        "name": "024",
        "percent": "27.8"
      },
      {
        "name": "021",
        "percent": "24.3"
      },
      {
        "name": "019",
        "percent": "24.3"
      },
      {
        "name": "065",
        "percent": "23.3"
      },
      {
        "name": "030",
        "percent": "23.2"
      },
      {
        "name": "054",
        "percent": "22.8"
      },
      {
        "name": "028",
        "percent": "21.3"
      },
      {
        "name": "060",
        "percent": "19.2"
      },
      {
        "name": "045",
        "percent": "18.1"
      },
      {
        "name": "056",
        "percent": "16.8"
      },
      {
        "name": "043",
        "percent": "16.7"
      },
      {
        "name": "053",
        "percent": "16.2"
      },
      {
        "name": "059",
        "percent": "15.9"
      },
      {
        "name": "058",
        "percent": "15.7"
      },
      {
        "name": "066",
        "percent": "15.0"
      },
      {
        "name": "074",
        "percent": "14.6"
      },
      {
        "name": "062",
        "percent": "13.7"
      },
      {
        "name": "046",
        "percent": "13.6"
      },
      {
        "name": "031",
        "percent": "13.3"
      },
      {
        "name": "068",
        "percent": "13.2"
      },
      {
        "name": "072",
        "percent": "12.6"
      },
      {
        "name": "055",
        "percent": "12.6"
      },
      {
        "name": "051",
        "percent": "12.5"
      },
      {
        "name": "061",
        "percent": "12.4"
      },
      {
        "name": "082",
        "percent": "12.0"
      },
      {
        "name": "079",
        "percent": "11.9"
      },
      {
        "name": "080",
        "percent": "11.8"
      },
      {
        "name": "070",
        "percent": "11.8"
      },
      {
        "name": "075",
        "percent": "11.5"
      },
      {
        "name": "057",
        "percent": "11.5"
      },
      {
        "name": "073",
        "percent": "11.3"
      },
      {
        "name": "022",
        "percent": "11.2"
      },
      {
        "name": "084",
        "percent": "11.0"
      },
      {
        "name": "032",
        "percent": "10.9"
      },
      {
        "name": "078",
        "percent": "10.5"
      },
      {
        "name": "087",
        "percent": "10.3"
      },
      {
        "name": "077",
        "percent": "10.3"
      },
      {
        "name": "088",
        "percent": "10.2"
      },
      {
        "name": "063",
        "percent": "10.1"
      },
      {
        "name": "092",
        "percent": "9.0"
      },
      {
        "name": "090",
        "percent": "8.7"
      },
      {
        "name": "086",
        "percent": "8.7"
      },
      {
        "name": "083",
        "percent": "8.5"
      },
      {
        "name": "093",
        "percent": "8.4"
      },
      {
        "name": "091",
        "percent": "7.7"
      },
      {
        "name": "033",
        "percent": "7.6"
      },
      {
        "name": "081",
        "percent": "6.5"
      },
      {
        "name": "067",
        "percent": "5.7"
      },
      {
        "name": "085",
        "percent": "5.4"
      },
      {
        "name": "064",
        "percent": "5.1"
      },
      {
        "name": "069",
        "percent": "4.2"
      },
      {
        "name": "023",
        "percent": "4.1"
      },
      {
        "name": "011",
        "percent": "3.9"
      },
      {
        "name": "071",
        "percent": "3.6"
      },
      {
        "name": "089",
        "percent": "2.9"
      },
      {
        "name": "076",
        "percent": "2.9"
      }
    ]
  }
}

================================================================================
ISteamUserStats.GetUserStatsForGame
--------------------------------------------------------------------------------
{
  "playerstats": {
    "achievements": [
      {
        "achieved": 1,
        "name": "001"
      },
      {
        "achieved": 1,
        "name": "002"
      },
      {
        "achieved": 1,
        "name": "003"
      },
      {
        "achieved": 1,
        "name": "004"
      },
      {
        "achieved": 1,
        "name": "005"
      },
      {
        "achieved": 1,
        "name": "006"
      },
      {
        "achieved": 1,
        "name": "007"
      },
      {
        "achieved": 1,
        "name": "008"
      },
      {
        "achieved": 1,
        "name": "009"
      },
      {
        "achieved": 1,
        "name": "010"
      },
      {
        "achieved": 1,
        "name": "012"
      },
      {
        "achieved": 1,
        "name": "013"
      },
      {
        "achieved": 1,
        "name": "014"
      },
      {
        "achieved": 1,
        "name": "015"
      },
      {
        "achieved": 1,
        "name": "016"
      },
      {
        "achieved": 1,
        "name": "017"
      },
      {
        "achieved": 1,
        "name": "018"
      },
      {
        "achieved": 1,
        "name": "024"
      },
      {
        "achieved": 1,
        "name": "025"
      },
      {
        "achieved": 1,
        "name": "026"
      },
      {
        "achieved": 1,
        "name": "027"
      },
      {
        "achieved": 1,
        "name": "028"
      },
      {
        "achieved": 1,
        "name": "029"
      },
      {
        "achieved": 1,
        "name": "030"
      },
      {
        "achieved": 1,
        "name": "034"
      },
      {
        "achieved": 1,
        "name": "035"
      },
      {
        "achieved": 1,
        "name": "036"
      },
      {
        "achieved": 1,
        "name": "037"
      },
      {
        "achieved": 1,
        "name": "038"
      },
      {
        "achieved": 1,
        "name": "039"
      },
      {
        "achieved": 1,
        "name": "040"
      },
      {
        "achieved": 1,
        "name": "041"
      },
      {
        "achieved": 1,
        "name": "042"
      },
      {
        "achieved": 1,
        "name": "044"
      },
      {
        "achieved": 1,
        "name": "047"
      },
      {
        "achieved": 1,
        "name": "048"
      },
      {
        "achieved": 1,
        "name": "049"
      },
      {
        "achieved": 1,
        "name": "050"
      },
      {
        "achieved": 1,
        "name": "052"
      },
      {
        "achieved": 1,
        "name": "054"
      },
      {
        "achieved": 1,
        "name": "065"
      },
      {
        "achieved": 1,
        "name": "070"
      },
      {
        "achieved": 1,
        "name": "060"
      },
      {
        "achieved": 1,
        "name": "079"
      },
      {
        "achieved": 1,
        "name": "080"
      },
      {
        "achieved": 1,
        "name": "081"
      },
      {
        "achieved": 1,
        "name": "082"
      },
      {
        "achieved": 1,
        "name": "083"
      },
      {
        "achieved": 1,
        "name": "084"
      },
      {
        "achieved": 1,
        "name": "087"
      },
      {
        "achieved": 1,
        "name": "088"
      }
    ],
    "gameName": "Assassin's Creed Odyssey",
    "steamID": "76561199077366346"
  }
}

================================================================================
ISteamUserStats.GetPlayerAchievements
--------------------------------------------------------------------------------
{
  "playerstats": {
    "achievements": [
      {
        "achieved": 1,
        "apiname": "001",
        "unlocktime": 1742468760
      },
      {
        "achieved": 1,
        "apiname": "002",
        "unlocktime": 1742477672
      },
      {
        "achieved": 1,
        "apiname": "003",
        "unlocktime": 1742486634
      },
      {
        "achieved": 1,
        "apiname": "004",
        "unlocktime": 1742542275
      },
      {
        "achieved": 1,
        "apiname": "005",
        "unlocktime": 1742553840
      },
      {
        "achieved": 1,
        "apiname": "006",
        "unlocktime": 1742680327
      },
      {
        "achieved": 1,
        "apiname": "007",
        "unlocktime": 1742680327
      },
      {
        "achieved": 1,
        "apiname": "008",
        "unlocktime": 1742727684
      },
      {
        "achieved": 1,
        "apiname": "009",
        "unlocktime": 1742731447
      },
      {
        "achieved": 1,
        "apiname": "010",
        "unlocktime": 1742731447
      },
      {
        "achieved": 0,
        "apiname": "011",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "012",
        "unlocktime": 1742477672
      },
      {
        "achieved": 1,
        "apiname": "013",
        "unlocktime": 1742478054
      },
      {
        "achieved": 1,
        "apiname": "014",
        "unlocktime": 1742469138
      },
      {
        "achieved": 1,
        "apiname": "015",
        "unlocktime": 1742469178
      },
      {
        "achieved": 1,
        "apiname": "016",
        "unlocktime": 1742800542
      },
      {
        "achieved": 1,
        "apiname": "017",
        "unlocktime": 1742812434
      },
      {
        "achieved": 1,
        "apiname": "018",
        "unlocktime": 1742804257
      },
      {
        "achieved": 0,
        "apiname": "019",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "020",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "021",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "022",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "023",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "024",
        "unlocktime": 1742807349
      },
      {
        "achieved": 1,
        "apiname": "025",
        "unlocktime": 1742804257
      },
      {
        "achieved": 1,
        "apiname": "026",
        "unlocktime": 1742798076
      },
      {
        "achieved": 1,
        "apiname": "027",
        "unlocktime": 1742723898
      },
      {
        "achieved": 1,
        "apiname": "028",
        "unlocktime": 1742538286
      },
      {
        "achieved": 1,
        "apiname": "029",
        "unlocktime": 1742673346
      },
      {
        "achieved": 1,
        "apiname": "030",
        "unlocktime": 1742805651
      },
      {
        "achieved": 0,
        "apiname": "031",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "032",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "033",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "034",
        "unlocktime": 1742723898
      },
      {
        "achieved": 1,
        "apiname": "035",
        "unlocktime": 1742566422
      },
      {
        "achieved": 1,
        "apiname": "036",
        "unlocktime": 1742799961
      },
      {
        "achieved": 1,
        "apiname": "037",
        "unlocktime": 1742478027
      },
      {
        "achieved": 1,
        "apiname": "038",
        "unlocktime": 1742469178
      },
      {
        "achieved": 1,
        "apiname": "039",
        "unlocktime": 1742536814
      },
      {
        "achieved": 1,
        "apiname": "040",
        "unlocktime": 1759996386
      },
      {
        "achieved": 1,
        "apiname": "041",
        "unlocktime": 1742712625
      },
      {
        "achieved": 1,
        "apiname": "042",
        "unlocktime": 1742477672
      },
      {
        "achieved": 0,
        "apiname": "043",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "044",
        "unlocktime": 1742534776
      },
      {
        "achieved": 0,
        "apiname": "045",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "046",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "047",
        "unlocktime": 1742727684
      },
      {
        "achieved": 1,
        "apiname": "048",
        "unlocktime": 1742535603
      },
      {
        "achieved": 1,
        "apiname": "049",
        "unlocktime": 1742539885
      },
      {
        "achieved": 1,
        "apiname": "050",
        "unlocktime": 1742681430
      },
      {
        "achieved": 0,
        "apiname": "051",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "052",
        "unlocktime": 1742971992
      },
      {
        "achieved": 0,
        "apiname": "053",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "054",
        "unlocktime": 1742971812
      },
      {
        "achieved": 0,
        "apiname": "055",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "056",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "064",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "065",
        "unlocktime": 1742532928
      },
      {
        "achieved": 0,
        "apiname": "066",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "067",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "068",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "057",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "058",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "069",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "070",
        "unlocktime": 1742971213
      },
      {
        "achieved": 0,
        "apiname": "071",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "072",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "073",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "059",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "060",
        "unlocktime": 1742811726
      },
      {
        "achieved": 0,
        "apiname": "074",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "075",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "076",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "077",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "078",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "061",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "062",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "079",
        "unlocktime": 1742981505
      },
      {
        "achieved": 1,
        "apiname": "080",
        "unlocktime": 1743081537
      },
      {
        "achieved": 1,
        "apiname": "081",
        "unlocktime": 1742982934
      },
      {
        "achieved": 1,
        "apiname": "082",
        "unlocktime": 1742981505
      },
      {
        "achieved": 1,
        "apiname": "083",
        "unlocktime": 1743083890
      },
      {
        "achieved": 0,
        "apiname": "063",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "084",
        "unlocktime": 1743084203
      },
      {
        "achieved": 0,
        "apiname": "085",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "086",
        "unlocktime": 0
      },
      {
        "achieved": 1,
        "apiname": "087",
        "unlocktime": 1760004959
      },
      {
        "achieved": 1,
        "apiname": "088",
        "unlocktime": 1760004959
      },
      {
        "achieved": 0,
        "apiname": "089",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "090",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "091",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "092",
        "unlocktime": 0
      },
      {
        "achieved": 0,
        "apiname": "093",
        "unlocktime": 0
      }
    ],
    "gameName": "Assassin's Creed Odyssey",
    "steamID": "76561199077366346",
    "success": true
  }
}

"""
