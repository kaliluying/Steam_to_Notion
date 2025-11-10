"""
Notion游戏列表客户端 (v2)
使用官方 Notion REST API (2025-09-03)
用于与Notion API交互，创建和管理游戏列表
"""
import typing as tp
from datetime import datetime
import time
import os

import requests

from ngl.errors import ServiceError, NotionApiError
from ngl.games.base import GameInfo

from .utils import echo, color


class NotionGameListV2:
    """
    Notion游戏列表管理类 (v2)
    使用官方 Notion REST API
    负责创建Notion数据库、导入游戏数据等操作
    """
    # 默认页面封面图片URL
    PAGE_COVER = "https://images.unsplash.com/photo-1559984430-c12e199879b6?ixlib=rb-1.2.1&q=85&fm=jpg&crop=entropy&cs=srgb&ixid=eyJhcHBfaWQiOjYzOTIxfQ"
    # 默认页面图标
    PAGE_ICON = "🎮"
    # API 版本（使用稳定版本）
    NOTION_VERSION = "2022-06-28"
    # API 基础URL
    API_BASE_URL = "https://api.notion.com/v1"

    def __init__(self, token: str, parent_page_id: tp.Optional[str] = None):
        """
        初始化Notion客户端
        
        Args:
            token: Notion API token (Integration token)
            parent_page_id: 父页面ID（可选，用于创建新数据库）
        """
        self.token = token
        self.parent_page_id = parent_page_id
        self._gl_icon = "👾"  # 游戏列表图标
        self._database_id = None
        self._db_properties_cache = None  # 缓存数据库属性
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json"
        }

    @classmethod
    def login(cls, token: tp.Optional[str] = None, parent_page_id: tp.Optional[str] = None):
        """
        登录Notion
        
        Args:
            token: Notion API token，如果为None则从环境变量或提示用户输入
            parent_page_id: 父页面ID（可选）
            
        Returns:
            NotionGameListV2实例
        """
        if token is None:
            token = os.getenv("NOTION_TOKEN")
            if not token:
                echo(color.y("登录Notion: ") + "https://www.notion.so/my-integrations")
                echo("创建 Integration 并获取 API token")
                token = input(color.c("Token: ")).strip()
        
        if parent_page_id is None:
            parent_page_id = os.getenv("NOTION_PAGE_ID")
        
        return cls(token=token, parent_page_id=parent_page_id)

    def _make_request(self, method: str, endpoint: str, max_retries: int = 3, **kwargs) -> requests.Response:
        """
        发送HTTP请求，带重试机制
        
        Args:
            method: HTTP方法 (GET, POST, PATCH等)
            endpoint: API端点（相对于API_BASE_URL）
            max_retries: 最大重试次数
            **kwargs: 传递给requests的参数
            
        Returns:
            requests.Response: 响应对象
            
        Raises:
            NotionApiError: API请求失败
        """
        url = f"{self.API_BASE_URL}/{endpoint.lstrip('/')}"
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, headers=self._headers, **kwargs)
                
                # 处理速率限制
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", retry_delay))
                    if attempt < max_retries - 1:
                        echo.y(f"速率限制，等待 {retry_after} 秒后重试 ({attempt + 1}/{max_retries})...")
                        time.sleep(retry_after)
                        continue
                
                # 处理其他错误
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("message", f"HTTP {response.status_code}")
                    raise NotionApiError(
                        msg=f"Notion API错误: {error_msg}",
                        error=response
                    )
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    echo.y(f"请求失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise NotionApiError(msg=f"请求失败: {e}", error=e)

    def create_game_page(self, title: str = "Steam Game Library", description: str = "My game list"):
        """
        创建Notion游戏列表数据库
        
        Args:
            title: 数据库标题
            description: 数据库描述（注意：新API中描述需要单独设置）
            
        Returns:
            dict: 包含数据库信息的字典，兼容旧接口
            
        Raises:
            NotionApiError: Notion API请求失败
        """
        if not self.parent_page_id:
            raise NotionApiError(
                msg="需要提供 parent_page_id 才能创建数据库。请通过环境变量 NOTION_PAGE_ID 或构造函数参数提供。"
            )
        
        echo.y("正在创建Notion数据库...")
        
        # 创建数据库
        try:
            schema = self._game_list_schema()
            echo.c(f"准备创建的属性架构: {list(schema.keys())}")
            
            database_response = self._make_request(
                "POST",
                "/databases",
                json={
                    "parent": {
                        "type": "page_id",
                        "page_id": self.parent_page_id
                    },
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": title
                            }
                        }
                    ],
                    "icon": {
                        "type": "emoji",
                        "emoji": self._gl_icon
                    },
                    "properties": schema
                }
            )
            
            database_data = database_response.json()
            self._database_id = database_data["id"]
            
            # 缓存数据库属性
            self._db_properties_cache = database_data.get("properties", {})
            echo.g(f"数据库创建成功: {self._database_id}")
            
            # 如果属性为空，尝试重新获取数据库信息
            if not self._db_properties_cache:
                echo.y("数据库属性为空，重新获取数据库信息...")
                time.sleep(0.5)  # 等待数据库完全创建
                db_get_response = self._make_request("GET", f"/databases/{self._database_id}")
                db_get_data = db_get_response.json()
                self._db_properties_cache = db_get_data.get("properties", {})
            
            if self._db_properties_cache:
                echo.c(f"数据库属性: {', '.join(self._db_properties_cache.keys())}")
            else:
                echo.r("错误：数据库属性仍然为空！")
                raise NotionApiError(msg="数据库创建成功但属性为空，请检查 API 版本和属性定义")
            
            # 返回兼容旧接口的字典
            return {
                "id": self._database_id,
                "collection": {
                    "id": self._database_id
                }
            }
            
        except Exception as e:
            raise NotionApiError(msg=f"创建Notion数据库失败: {e}", error=e)

    def connect_database(self, database_id: str):
        """
        连接到已存在的数据库
        
        Args:
            database_id: 数据库ID
        """
        self._database_id = database_id
        # 获取并缓存数据库属性
        db_response = self._make_request("GET", f"/databases/{database_id}")
        db_data = db_response.json()
        self._db_properties_cache = db_data.get("properties", {})
        echo.g(f"已连接到数据库: {database_id}")
        echo.c(f"数据库属性: {', '.join(self._db_properties_cache.keys())}")

    def get_existing_game_names(self) -> tp.Set[str]:
        """
        获取数据库中已有的游戏名称集合（用于去重）
        
        Returns:
            Set[str]: 已有游戏名称的集合
        """
        if not self._database_id:
            raise NotionApiError(msg="数据库ID未设置，请先创建或连接数据库")
        
        # 获取数据库属性以找到标题属性名称
        if self._db_properties_cache is None:
            db_response = self._make_request("GET", f"/databases/{self._database_id}")
            db_data = db_response.json()
            self._db_properties_cache = db_data.get("properties", {})
        
        db_properties = self._db_properties_cache
        
        # 找到标题属性的实际名称
        title_prop_name = None
        for prop_name, prop_data in db_properties.items():
            if prop_data.get("type") == "title":
                title_prop_name = prop_name
                break
        
        if not title_prop_name:
            raise NotionApiError(msg="数据库中未找到标题属性")
        
        existing_names = set()
        next_cursor = None
        
        # 分页查询所有页面
        while True:
            query_payload = {
                "page_size": 100  # Notion API 最大页面大小
            }
            if next_cursor:
                query_payload["start_cursor"] = next_cursor
            
            response = self._make_request(
                "POST",
                f"/databases/{self._database_id}/query",
                json=query_payload
            )
            data = response.json()
            
            # 提取游戏名称
            for page in data.get("results", []):
                properties = page.get("properties", {})
                title_prop = properties.get(title_prop_name, {})
                title_array = title_prop.get("title", [])
                if title_array:
                    game_name = title_array[0].get("text", {}).get("content", "").strip()
                    if game_name:
                        existing_names.add(game_name)
            
            # 检查是否有更多页面
            next_cursor = data.get("next_cursor")
            if not next_cursor:
                break
        
        return existing_names

    @staticmethod
    def _parse_date(game: GameInfo) -> tp.Optional[str]:
        """
        解析游戏发布日期字符串为日期字符串 (YYYY-MM-DD)
        
        Args:
            game: 游戏信息对象
            
        Returns:
            str: 日期字符串 (YYYY-MM-DD) 或 None
        """
        date_str = game.release_date
        if not date_str:
            return None
        
        # 俄语月份映射
        russian_months = {
            'янв.': 'Jan', 'фев.': 'Feb', 'мар.': 'Mar', 'апр.': 'Apr',
            'май': 'May', 'июн.': 'Jun', 'июл.': 'Jul', 'авг.': 'Aug',
            'сен.': 'Sep', 'окт.': 'Oct', 'ноя.': 'Nov', 'дек.': 'Dec'
        }
        
        # 清理日期字符串
        cleaned_date = date_str.strip()
        
        # 处理俄语格式：移除"г."后缀
        if cleaned_date.endswith(' г.'):
            cleaned_date = cleaned_date[:-3].strip()
        
        # 替换俄语月份为英语月份
        for ru_month, en_month in russian_months.items():
            if ru_month in cleaned_date:
                cleaned_date = cleaned_date.replace(ru_month, en_month)
                break
        
        # 支持的日期格式列表（按常见程度排序）
        check_date_formats = (
            r"%d %b, %Y",      # "24 Feb, 2022"
            r"%d. %b %Y",      # "16. Nov 2004"
            r"%d.%b.%Y",       # "16.Nov.2004" (无空格)
            r"%d. %b. %Y",     # "16. Nov. 2004"
            r"%b %d, %Y",      # "Feb 24, 2022"
            r"%b %d %Y",       # "Feb 24 2022"
            r"%d %b %Y",       # "24 Feb 2022"
            r"%b %Y",          # "Feb 2022"
            r"%Y"              # "2022"
        )
        
        for fmt in check_date_formats:
            try:
                parsed_date = datetime.strptime(cleaned_date, fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # 如果所有格式都解析失败，输出警告并返回None
        echo.r(
            f"\n游戏 '{game.name}:{game.id}' | 发布日期: '{date_str}' 不匹配任何格式 | 跳过"
        )
        return None

    def add_game(self, game: GameInfo, game_page: tp.Any = None, use_bg_as_cover: bool = False, skip_if_exists: bool = False, existing_names: tp.Optional[tp.Set[str]] = None) -> bool:
        """
        向Notion游戏列表中添加一个游戏
        
        Args:
            game: 游戏信息对象
            game_page: 兼容参数（新API中不需要）
            use_bg_as_cover: 是否使用背景图片作为封面
            skip_if_exists: 如果游戏已存在则跳过（不添加）
            existing_names: 已有游戏名称集合（用于快速检查，如果为None则会在需要时查询）
            
        Returns:
            bool: 是否添加成功（如果因为已存在而跳过，返回True）
        """
        if not self._database_id:
            raise NotionApiError(msg="数据库ID未设置，请先创建或连接数据库")
        
        # 检查是否已存在
        if skip_if_exists:
            if existing_names is None:
                existing_names = self.get_existing_game_names()
            if game.name in existing_names:
                return True  # 已存在，跳过但不视为错误
        
        try:
            # 获取数据库属性（使用缓存或重新获取）
            if self._db_properties_cache is None:
                db_response = self._make_request("GET", f"/databases/{self._database_id}")
                db_data = db_response.json()
                self._db_properties_cache = db_data.get("properties", {})
            
            db_properties = self._db_properties_cache
            
            # 找到标题属性的实际名称（通常是第一个title类型的属性）
            title_prop_name = None
            for prop_name, prop_data in db_properties.items():
                if prop_data.get("type") == "title":
                    title_prop_name = prop_name
                    break
            
            if not title_prop_name:
                raise NotionApiError(msg="数据库中未找到标题属性")
            
            # 准备属性数据，使用实际的属性名称
            properties = {
                title_prop_name: {
                    "type": "title",
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": game.name
                            }
                        }
                    ]
                }
            }
            
            # 添加平台属性（如果存在）
            if "平台" in db_properties:
                properties["平台"] = {
                    "type": "multi_select",
                    "multi_select": [
                        {"name": platform} for platform in game.platforms
                    ]
                }
            
            # 添加游戏时长属性（如果存在）- 转换为小时
            if "游戏时长(小时)" in db_properties:
                playtime_hours = round(game.playtime_minutes / 60, 2) if game.playtime_minutes else 0
                properties["游戏时长(小时)"] = {
                    "type": "number",
                    "number": playtime_hours
                }
            
            # 添加发布日期（如果存在）
            if "发行日期" in db_properties:
                release_date = self._parse_date(game)
                if release_date:
                    properties["发行日期"] = {
                        "type": "date",
                        "date": {
                            "start": release_date
                        }
                    }
            
            # 添加备注（如果存在）
            if "备注" in db_properties and game.playtime:
                properties["备注"] = {
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"游戏时长(小时): {game.playtime}"
                            }
                        }
                    ]
                }
            
            # 构建请求体
            payload = {
                "parent": {
                    "database_id": self._database_id
                },
                "properties": properties
            }
            
            # 添加图标
            icon_uri = game.icon_uri or game.logo_uri
            if icon_uri:
                payload["icon"] = {
                    "type": "external",
                    "external": {
                        "url": icon_uri
                    }
                }
            
            # 添加封面
            cover_img_uri = game.bg_uri or game.logo_uri if use_bg_as_cover else game.logo_uri
            if cover_img_uri:
                payload["cover"] = {
                    "type": "external",
                    "external": {
                        "url": cover_img_uri
                    }
                }
            
            # 创建页面
            response = self._make_request("POST", "/pages", json=payload)
            page_data = response.json()
            
            return True
            
        except Exception as e:
            echo.r(f"添加游戏 '{game.name}' 失败: {e}")
            return False

    def import_game_list(self, game_list: tp.List[GameInfo], game_page: tp.Any = None, skip_duplicates: bool = True, **kwargs) -> tp.List[GameInfo]:
        """
        批量导入游戏列表到Notion
        
        Args:
            game_list: 游戏信息列表
            game_page: 兼容参数（新API中不需要）
            skip_duplicates: 是否跳过已存在的游戏（默认True）
            **kwargs: 其他参数（如use_bg_as_cover）
            
        Returns:
            List[GameInfo]: 导入失败的游戏列表
        """
        errors = []
        skipped = []
        total = len(game_list)
        
        # 如果需要去重，先获取已有游戏名称
        existing_names = None
        if skip_duplicates:
            echo.y("正在查询已有游戏...")
            try:
                existing_names = self.get_existing_game_names()
                echo.g(f"数据库中已有 {len(existing_names)} 个游戏")
            except Exception as e:
                echo.r(f"查询已有游戏失败: {e}，将继续导入但可能产生重复")
                skip_duplicates = False
        
        imported_count = 0
        skipped_count = 0
        
        for i, game in enumerate(game_list, start=1):
            # 检查是否已存在
            if skip_duplicates and existing_names and game.name in existing_names:
                skipped_count += 1
                skipped.append(game)
                echo.c(f"进度: {i}/{total} (已导入: {imported_count}, 已跳过: {skipped_count})", end="\r")
                continue
            
            if self.add_game(game, game_page, skip_if_exists=skip_duplicates, existing_names=existing_names, **kwargs):
                imported_count += 1
                echo.c(f"进度: {i}/{total} (已导入: {imported_count}, 已跳过: {skipped_count})", end="\r")
            else:
                errors.append(game)
            
            # 添加延迟以避免速率限制
            if i < total:
                time.sleep(0.3)
        
        echo.m("")  # 换行
        if skipped_count > 0:
            echo.y(f"已跳过 {skipped_count} 个已存在的游戏")
        
        return errors

    @staticmethod
    def _game_list_schema():
        """
        获取游戏列表数据库的属性架构定义（中文）
        
        Returns:
            dict: 数据库属性架构字典
        """
        return {
            "游戏名": {
                "title": {}
            },
            "状态": {
                "select": {
                    "options": [
                        {"name": "通关", "color": "green"},
                        {"name": "游玩中", "color": "yellow"},
                        {"name": "计划中", "color": "blue"},
                        {"name": "吃灰", "color": "gray"},
                        {"name": "弃坑", "color": "red"}
                    ]
                }
            },
            "平台": {
                "multi_select": {
                    "options": [
                        {"name": "Steam", "color": "gray"},
                        {"name": "PC", "color": "default"},
                        {"name": "Switch", "color": "red"},
                        {"name": "PlayStation", "color": "blue"},
                        {"name": "Xbox", "color": "green"}
                    ]
                }
            },
            "发行日期": {
                "date": {}
            },
            "游戏时长(小时)": {
                "number": {
                    "format": "number"
                }
            },
            "备注": {
                "rich_text": {}
            }
        }

