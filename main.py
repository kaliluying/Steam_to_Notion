"""
主程序入口文件
用于将Steam游戏库导入到Notion中

Copyright (c) 2020 solesensei
Copyright (c) 2025 kaliluying

MIT License
"""

import logging
import os
import sys
from operator import attrgetter
from pathlib import Path

from dotenv import load_dotenv

from src.client_v2 import NotionGameListV2 as NotionGameList
from src.errors import ServiceError
from src.games.steam import SteamGamesLibrary
from src.logging_config import setup_logging
from src.utils import echo, soft_exit

# 加载 .env 文件
# 支持打包成exe后的路径：优先使用exe所在目录，否则使用脚本所在目录
if getattr(sys, "frozen", False):
    # 打包成exe后的情况
    base_path = Path(sys.executable).parent
else:
    # 正常Python脚本运行
    base_path = Path(__file__).parent
env_path = base_path / ".env"
load_dotenv(env_path)

# 配置日志 (仅文件输出)
setup_logging(log_file="steam_to_notion.log", level=logging.INFO)

# ----------- 从 .env 文件读取配置 -----------
# Notion 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # 可选：已有数据库ID

# Steam 配置（用于验证，实际使用时会从环境变量读取）
STEAM_TOKEN = os.getenv("STEAM_TOKEN")
STEAM_USER = os.getenv("STEAM_USER")  # login() 方法会自动处理转换


def parse_bool_env(value: str) -> bool:
    """解析布尔类型环境变量"""
    return value and value.lower() in ("true", "1", "yes", "on")


# 导入选项（布尔值，从字符串转换）
STORE_BG_COVER = parse_bool_env(os.getenv("STORE_BG_COVER", "false"))
SKIP_NON_STEAM = parse_bool_env(os.getenv("SKIP_NON_STEAM", "false"))
USE_ONLY_LIBRARY = parse_bool_env(os.getenv("USE_ONLY_LIBRARY", "false"))
SKIP_FREE_STEAM = parse_bool_env(os.getenv("SKIP_FREE_STEAM", "false"))
UPDATE_MODE = parse_bool_env(os.getenv("UPDATE_MODE", "false"))

# 测试限制（可选）
try:
    TEST_LIMIT = int(os.getenv("TEST_LIMIT", "0")) or None
except ValueError:
    TEST_LIMIT = None

# 调试模式
DEBUG = parse_bool_env(os.getenv("DEBUG", "false"))
# ---------------------------------

try:
    # 验证必需的配置
    required_configs = {
        "NOTION_TOKEN": NOTION_TOKEN,
        "STEAM_TOKEN": STEAM_TOKEN,
        "STEAM_USER": STEAM_USER,
    }
    for name, value in required_configs.items():
        if not value:
            raise ServiceError(message=f"未配置 {name}，请在 .env 文件中设置")

    # 验证参数组合的有效性
    if SKIP_NON_STEAM and USE_ONLY_LIBRARY:
        raise ServiceError(
            message="不能同时设置 SKIP_NON_STEAM 和 USE_ONLY_LIBRARY 为 true"
        )

    # 登录Notion
    echo.y("正在登录Notion...")
    if not NOTION_DATABASE_ID and not NOTION_PAGE_ID:
        raise ServiceError(
            message="未配置 NOTION_PAGE_ID 或 NOTION_DATABASE_ID，请在 .env 文件中设置至少一个"
        )
    ngl = NotionGameList.login()
    echo.g("Notion登录成功！")

    # 登录Steam
    echo.y("正在登录Steam...")
    steam = SteamGamesLibrary.login()
    echo.g("Steam登录成功！")

    # 获取Steam游戏库列表
    echo.y("正在获取Steam游戏库...")
    if TEST_LIMIT:
        echo.y(f"测试模式：限制获取 {TEST_LIMIT} 个游戏")
    # 先获取所有游戏ID列表，这会填充缓存
    game_ids = steam.get_games_list(
        skip_non_steam=SKIP_NON_STEAM,
        skip_free_games=SKIP_FREE_STEAM,
        library_only=USE_ONLY_LIBRARY,
        limit=TEST_LIMIT,
    )
    # 从缓存中获取游戏信息
    game_list = sorted(
        [steam._games[str(id_)] for id_ in game_ids],
        key=attrgetter("playtime_minutes"),
        reverse=True,
    )
    if not game_list:
        raise ServiceError(message="未找到Steam游戏")

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
        ngl.create_game_page()
        echo.g("创建成功！")

    # 将Steam游戏库导入到Notion
    echo.y("正在将Steam游戏库导入到Notion...")
    errors = ngl.import_game_list(
        game_list,
        None,
        skip_duplicates=not UPDATE_MODE,
        update_mode=UPDATE_MODE,
        use_bg_as_cover=STORE_BG_COVER,
    )
    imported = len(game_list) - len(errors)

    if imported == 0:
        raise ServiceError(message="没有游戏被导入到Notion")

    # 显示导入失败的游戏
    if errors:
        echo.r("未导入的游戏: ")
        for error in sorted(errors, key=lambda x: x.name):
            echo.r(f"- {error.name}")
    echo.g(f"已导入: {imported}/{len(game_list)}")

    # 导入成功后删除缓存
    cache_file = Path(steam.CACHE_GAME_FILE)
    if cache_file.exists():
        cache_file.unlink()
        echo.g(f"已删除缓存文件: {cache_file}")

except (ServiceError, KeyboardInterrupt, Exception) as err:
    if isinstance(err, ServiceError):
        echo(err)
    elif isinstance(err, KeyboardInterrupt):
        echo.y("\n用户取消操作")
        soft_exit(0)
    else:
        echo(f"\n{err.__class__.__name__}: {err}", file=sys.stderr)
    if DEBUG:
        raise err
    soft_exit(1)

echo.m("完成！")
soft_exit(0)
