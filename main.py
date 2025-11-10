"""
主程序入口文件
用于将Steam游戏库导入到Notion中
"""
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from ngl.client_v2 import NotionGameListV2 as NotionGameList
from ngl.errors import ServiceError
from ngl.games.steam import SteamGamesLibrary
from ngl.utils import echo, color, soft_exit

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# ----------- 从 .env 文件读取配置 -----------
# Notion 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # 可选：已有数据库ID

# Steam 配置
STEAM_TOKEN = os.getenv("STEAM_TOKEN")
STEAM_USER_STR = os.getenv("STEAM_USER")
# Steam用户ID可能是数字ID或自定义URL，需要转换
if STEAM_USER_STR:
    # 如果是纯数字，转换为整数（Steam 64位ID）
    if STEAM_USER_STR.strip().isdigit():
        STEAM_USER = int(STEAM_USER_STR.strip())
    else:
        # 否则作为自定义URL处理（移除URL前缀）
        STEAM_USER = STEAM_USER_STR.strip()
        # 移除可能的URL前缀
        STEAM_USER = re.sub(r"^https?:\/\/steamcommunity\.com\/id\/", "", STEAM_USER)
else:
    STEAM_USER = None

# 导入选项（布尔值，从字符串转换）
STORE_BG_COVER = os.getenv("STORE_BG_COVER", "false").lower() in ("true", "1", "yes", "on")
SKIP_NON_STEAM = os.getenv("SKIP_NON_STEAM", "false").lower() in ("true", "1", "yes", "on")
USE_ONLY_LIBRARY = os.getenv("USE_ONLY_LIBRARY", "false").lower() in ("true", "1", "yes", "on")
SKIP_FREE_STEAM = os.getenv("SKIP_FREE_STEAM", "false").lower() in ("true", "1", "yes", "on")
STEAM_NO_CACHE = os.getenv("STEAM_NO_CACHE", "false").lower() in ("true", "1", "yes", "on")
ALLOW_DUPLICATES = os.getenv("ALLOW_DUPLICATES", "false").lower() in ("true", "1", "yes", "on")

# 测试限制（可选）
TEST_LIMIT = os.getenv("TEST_LIMIT")
if TEST_LIMIT:
    try:
        TEST_LIMIT = int(TEST_LIMIT)
    except ValueError:
        TEST_LIMIT = None
else:
    TEST_LIMIT = None

# 调试模式
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
# ---------------------------------

try:
    # 验证必需的配置
    if not NOTION_TOKEN:
        raise ServiceError(msg="未配置 NOTION_TOKEN，请在 .env 文件中设置")
    if not STEAM_TOKEN:
        raise ServiceError(msg="未配置 STEAM_TOKEN，请在 .env 文件中设置")
    if not STEAM_USER:
        raise ServiceError(msg="未配置 STEAM_USER，请在 .env 文件中设置")

    # 验证参数组合的有效性
    if SKIP_NON_STEAM and USE_ONLY_LIBRARY:
        raise ServiceError(msg="不能同时设置 SKIP_NON_STEAM 和 USE_ONLY_LIBRARY 为 true")

    # 登录Notion
    echo.y("正在登录Notion...")
    # 如果使用已有数据库，NOTION_PAGE_ID 不是必需的
    if not NOTION_DATABASE_ID and not NOTION_PAGE_ID:
        raise ServiceError(msg="未配置 NOTION_PAGE_ID 或 NOTION_DATABASE_ID，请在 .env 文件中设置至少一个")
    ngl = NotionGameList.login(token=NOTION_TOKEN, parent_page_id=NOTION_PAGE_ID)
    echo.g("Notion登录成功！")
    
    # 登录Steam
    echo.y("正在登录Steam...")
    steam = SteamGamesLibrary.login(api_key=STEAM_TOKEN, user_id=STEAM_USER)
    echo.g("Steam登录成功！")

    # 获取Steam游戏库列表
    echo.y("正在获取Steam游戏库...")
    game_list = sorted(
        [
            steam.get_game_info(id_) for id_ in steam.get_games_list(
                skip_non_steam=SKIP_NON_STEAM,
                skip_free_games=SKIP_FREE_STEAM,
                library_only=USE_ONLY_LIBRARY,
                no_cache=STEAM_NO_CACHE,
            )
        ], key=lambda x: x.playtime_minutes or 0, reverse=True  # 按游戏时长从高到低排序
    )
    if not game_list:
        raise ServiceError(msg="未找到Steam游戏")

    echo.m(" " * 100 + f"\r已获取 {len(game_list)} 个游戏！")

    # 连接或创建Notion数据库
    if NOTION_DATABASE_ID:
        # 连接到已有数据库
        echo.y("正在连接到已有Notion数据库...")
        ngl.connect_database(NOTION_DATABASE_ID)
        echo.g("连接成功！")
    else:
        # 创建新数据库
        echo.y("正在创建Notion模板页面...")
        game_page = ngl.create_game_page()
        echo.g("创建成功！")
    
    # 测试模式：限制导入数量
    if TEST_LIMIT and TEST_LIMIT > 0 and len(game_list) > TEST_LIMIT:
        echo.y(f"测试模式：只导入前 {TEST_LIMIT} 个游戏（共 {len(game_list)} 个）")
        game_list = game_list[:TEST_LIMIT]
    
    # 将Steam游戏库导入到Notion
    echo.y("正在将Steam游戏库导入到Notion...")
    # skip_duplicates: 默认跳过重复，除非在 .env 中设置 ALLOW_DUPLICATES=true
    errors = ngl.import_game_list(
        game_list, 
        None, 
        skip_duplicates=not ALLOW_DUPLICATES,
        use_bg_as_cover=STORE_BG_COVER
    )
    imported = len(game_list) - len(errors)

    if imported == 0:
        raise ServiceError(msg="没有游戏被导入到Notion")

    # 显示导入失败的游戏
    if errors:
        echo.r("未导入的游戏: ")
        for error in sorted(errors, key=lambda x: x.name):
            echo.r(f"- {error.name}")
    echo.g(f"已导入: {imported}/{len(game_list)}\n")

except ServiceError as err:
    # 处理服务错误
    echo(err)
    if DEBUG:
        raise err
    soft_exit(1)
except (Exception, KeyboardInterrupt) as err:
    # 处理其他异常和用户中断
    echo(f"\n{err.__class__.__name__}: {err}", file=sys.stderr)
    if DEBUG:
        raise err
    soft_exit(1)

echo.m("完成！")
soft_exit(0)
