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


import dateparser

from src.errors import ServiceError, NotionApiError, DataParseError
from src.games.base import GameInfo

from src.utils import echo, color


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
    # API 版本（使用最新稳定版本）
    NOTION_VERSION = "2025-09-03"
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
        self._is_new_database = False  # 标记数据库是否为新建的
        self._data_source_id = None  # 数据源ID（用于新API版本）
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
        }

    @classmethod
    def login(
        cls, token: tp.Optional[str] = None, parent_page_id: tp.Optional[str] = None
    ):
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

    def _make_request(
        self, method: str, endpoint: str, max_retries: int = 3, **kwargs
    ) -> requests.Response:
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
                response = requests.request(
                    method, url, headers=self._headers, **kwargs
                )

                # 处理速率限制
                if response.status_code == 429:
                    retry_after_header = response.headers.get("Retry-After")
                    try:
                        retry_after = (
                            int(retry_after_header)
                            if retry_after_header
                            else retry_delay
                        )
                    except ValueError:
                        retry_after = retry_delay
                    if attempt < max_retries - 1:
                        echo.y(
                            f"速率限制，等待 {retry_after} 秒后重试 ({attempt + 1}/{max_retries})..."
                        )
                        time.sleep(retry_after)
                        continue
                    else:
                        raise NotionApiError(
                            message=f"Notion API 速率限制，已达最大重试次数",
                            code=429,
                            details={"url": url, "method": method},
                        )

                # 处理其他错误
                if response.status_code >= 400:
                    try:
                        error_data = response.json() if response.content else {}
                    except Exception:
                        error_data = {
                            "message": f"HTTP {response.status_code}, 响应解析失败"
                        }
                    error_msg = error_data.get(
                        "message", f"HTTP {response.status_code}"
                    )
                    raise NotionApiError(
                        message=f"Notion API错误: {error_msg}",
                        code=response.status_code,
                        details={"url": url, "method": method},
                        original_exception=None,
                    )

                return response

            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    echo.y(
                        f"请求超时，{retry_delay}秒后重试 ({attempt + 1}/{max_retries}): {e}"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise NotionApiError(
                    message=f"Notion API 请求超时",
                    code=408,
                    details={"url": url, "method": method},
                    original_exception=e,
                ) from e
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    echo.y(
                        f"连接失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries}): {e}"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise NotionApiError(
                    message=f"Notion API 连接失败",
                    code=503,
                    details={"url": url, "method": method},
                    original_exception=e,
                ) from e
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    echo.y(
                        f"请求失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries}): {e}"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise NotionApiError(
                    message=f"Notion API 请求失败: {e}",
                    code=503,
                    details={"url": url, "method": method},
                    original_exception=e,
                ) from e
            except Exception as e:
                raise NotionApiError(
                    message=f"Notion API 请求失败: {e}",
                    code=500,
                    details={"url": url, "method": method},
                    original_exception=e,
                ) from e

    def create_game_page(
        self, title: str = "Steam Game Library", description: str = "My game list"
    ):
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
                message="需要提供 parent_page_id 才能创建数据库。请通过环境变量 NOTION_PAGE_ID 或构造函数参数提供。",
                code=400,
            )

        echo.y("正在创建Notion数据库...")

        # 创建数据库
        try:
            schema = self._game_list_schema()
            echo.c(f"准备创建的属性架构: {list(schema.keys())}")

            # 使用 2025-09-03 API 版本的新格式：属性定义在 initial_data_source 下
            database_response = self._make_request(
                "POST",
                "/databases",
                json={
                    "parent": {"type": "page_id", "page_id": self.parent_page_id},
                    "title": [{"type": "text", "text": {"content": title}}],
                    "icon": {"type": "emoji", "emoji": self._gl_icon},
                    "initial_data_source": {"properties": schema},
                },
            )

            database_data = database_response.json()
            self._database_id = database_data["id"]
            self._is_new_database = True  # 标记为新创建的数据库

            # 缓存数据库属性
            # 2025-09-03 版本：属性可能在 properties 中（向后兼容）或需要从 data_sources 获取
            self._db_properties_cache = database_data.get("properties", {})

            # 如果属性为空，尝试从 data_sources 获取（新版本格式）
            if not self._db_properties_cache and "data_sources" in database_data:
                echo.y("从 data_sources 获取属性...")
                self._db_properties_cache = self._fetch_properties_from_data_source(
                    database_data.get("data_sources", [])
                )
            elif "data_sources" in database_data:
                # 即使属性不为空，也保存 data_source_id（用于查询）
                data_sources = database_data.get("data_sources", [])
                if data_sources:
                    self._data_source_id = data_sources[0].get("id")

            echo.g(f"数据库创建成功: {self._database_id}")

            # 如果属性仍然为空，尝试重新获取数据库信息
            if not self._db_properties_cache:
                echo.y("数据库属性为空，重新获取数据库信息...")
                time.sleep(0.5)  # 等待数据库完全创建
                db_get_response = self._make_request(
                    "GET", f"/databases/{self._database_id}"
                )
                db_get_data = db_get_response.json()
                self._db_properties_cache = db_get_data.get("properties", {})
                # 重新获取时也检查 data_sources
                if "data_sources" in db_get_data:
                    data_sources = db_get_data.get("data_sources", [])
                    if data_sources:
                        self._data_source_id = data_sources[0].get("id")

            if self._db_properties_cache:
                echo.c(f"数据库属性: {', '.join(self._db_properties_cache.keys())}")
            else:
                echo.r("错误：数据库属性仍然为空！")
                raise NotionApiError(
                    message="数据库创建成功但属性为空，请检查 API 版本和属性定义",
                    code=500,
                    details={"database_id": self._database_id},
                )

            # 返回兼容旧接口的字典
            return {"id": self._database_id, "collection": {"id": self._database_id}}

        except NotionApiError:
            raise
        except Exception as e:
            raise NotionApiError(
                message=f"创建Notion数据库失败: {e}",
                code=500,
                details={"parent_page_id": self.parent_page_id},
                original_exception=e,
            ) from e

    def _get_title_property_name(self, db_properties: dict) -> tp.Optional[str]:
        """
        从数据库属性中查找标题属性名称

        Args:
            db_properties: 数据库属性字典

        Returns:
            str: 标题属性名称，如果未找到则返回 None
        """
        for prop_name, prop_data in db_properties.items():
            if prop_data.get("type") == "title":
                return prop_name
        return None

    def _ensure_db_properties_cache(self) -> dict:
        """
        确保数据库属性缓存已加载

        Returns:
            dict: 数据库属性字典
        """
        if self._db_properties_cache is None:
            db_response = self._make_request("GET", f"/databases/{self._database_id}")
            self._db_properties_cache = db_response.json().get("properties", {})
        return self._db_properties_cache

    def _build_game_properties(
        self, game: GameInfo, db_properties: dict, include_title: bool = False
    ) -> dict:
        """
        构建游戏属性字典

        Args:
            game: 游戏信息对象
            db_properties: 数据库属性字典
            include_title: 是否包含标题属性

        Returns:
            dict: 游戏属性字典
        """
        properties = {}

        if include_title:
            title_prop_name = self._get_title_property_name(db_properties)
            if title_prop_name:
                properties[title_prop_name] = {
                    "type": "title",
                    "title": [{"type": "text", "text": {"content": game.name}}],
                }

        if "平台" in db_properties:
            properties["平台"] = {
                "type": "multi_select",
                "multi_select": [{"name": platform} for platform in game.platforms],
            }

        if "游戏时长(小时)" in db_properties:
            playtime_hours = (
                round(game.playtime_minutes / 60, 2) if game.playtime_minutes else 0
            )
            properties["游戏时长(小时)"] = {"type": "number", "number": playtime_hours}

        if "发行日期" in db_properties:
            release_date = self._parse_date(game)
            if release_date:
                properties["发行日期"] = {
                    "type": "date",
                    "date": {"start": release_date},
                }

        if "备注" in db_properties and game.playtime:
            properties["备注"] = {
                "type": "rich_text",
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"游戏时长(小时): {game.playtime}"},
                    }
                ],
            }

        return properties

    def _build_cover_payload(self, game: GameInfo, use_bg_as_cover: bool) -> dict:
        """
        构建封面和图标的 payload

        Args:
            game: 游戏信息对象
            use_bg_as_cover: 是否使用背景图作为封面

        Returns:
            dict: 包含 icon 和 cover 的 payload 字典
        """
        payload = {}

        icon_uri = game.icon_uri or game.logo_uri
        if icon_uri:
            payload["icon"] = {"type": "external", "external": {"url": icon_uri}}

        cover_img_uri = game.bg_uri if use_bg_as_cover else game.logo_uri
        if cover_img_uri:
            payload["cover"] = {"type": "external", "external": {"url": cover_img_uri}}

        return payload

    def _fetch_properties_from_data_source(self, data_sources: tp.List[dict]) -> dict:
        """
        从 data_sources 获取属性（新版 API）

        Args:
            data_sources: 数据源列表

        Returns:
            dict: 属性字典
        """
        if not data_sources:
            return {}
        data_source_id = data_sources[0].get("id")
        if not data_source_id:
            return {}
        self._data_source_id = data_source_id
        try:
            ds_response = self._make_request("GET", f"/data_sources/{data_source_id}")
            return ds_response.json().get("properties", {})
        except Exception as e:
            echo.y(f"从 data_source 获取属性失败: {e}")
            return {}

    def connect_database(self, database_id: str):
        """
        连接到已存在的数据库

        Args:
            database_id: 数据库ID
        """
        self._database_id = database_id
        self._is_new_database = False  # 标记为已存在的数据库
        # 获取并缓存数据库属性
        db_response = self._make_request("GET", f"/databases/{database_id}")
        db_data = db_response.json()
        self._db_properties_cache = db_data.get("properties", {})
        echo.g(f"已连接到数据库: {database_id}")

        # 如果属性为空，尝试从 data_sources 获取（新版本格式 2025-09-03）
        if not self._db_properties_cache and "data_sources" in db_data:
            echo.y("从 data_sources 获取属性...")
            self._db_properties_cache = self._fetch_properties_from_data_source(
                db_data.get("data_sources", [])
            )
            if self._db_properties_cache:
                echo.g("成功从 data_sources 获取属性")
        elif "data_sources" in db_data:
            # 即使属性不为空，也保存 data_source_id（用于查询）
            data_sources = db_data.get("data_sources", [])
            if data_sources:
                self._data_source_id = data_sources[0].get("id")

        # 检查属性是否为空
        if not self._db_properties_cache:
            echo.r("警告：数据库属性为空！")
            echo.y("这可能是因为：")
            echo.y("1. 数据库没有定义任何属性")
            echo.y("2. API 响应格式不同，请检查 Notion API 版本")
            echo.y("3. 数据库权限不足")
            # 尝试打印完整的响应以便调试
            debug_mode = os.getenv("DEBUG", "false").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )
            if debug_mode:
                echo.c(f"数据库响应: {db_data}")
        else:
            echo.c(f"数据库属性: {', '.join(self._db_properties_cache.keys())}")

        # 验证是否有标题属性
        title_prop_name = None
        for prop_name, prop_data in self._db_properties_cache.items():
            if prop_data.get("type") == "title":
                title_prop_name = prop_name
                break

        if not title_prop_name:
            echo.r("错误：数据库中未找到标题类型的属性！")
            echo.y("Notion 数据库必须包含至少一个标题类型的属性才能添加页面。")
            echo.y(
                "请在 Notion 中为数据库添加一个标题类型的属性（通常是 'Name' 或 '游戏名'）。"
            )
            raise NotionApiError(
                message="数据库中未找到标题属性，无法添加游戏。请先在 Notion 中为数据库添加一个标题类型的属性。"
            )

    def get_existing_game_names(self) -> tp.Set[str]:
        """
        获取数据库中已有的游戏名称集合（用于去重）

        Returns:
            Set[str]: 已有游戏名称的集合
        """
        game_map = self.get_existing_game_map()
        return set(game_map.keys())

    def get_existing_game_map(self) -> tp.Dict[str, str]:
        """
        获取数据库中已有的游戏名称到页面ID的映射（用于更新模式）

        Returns:
            Dict[str, str]: 游戏名称到页面ID的映射
        """
        if not self._database_id:
            raise NotionApiError(message="数据库ID未设置，请先创建或连接数据库")

        # 获取数据库属性以找到标题属性名称
        db_properties = self._ensure_db_properties_cache()

        # 找到标题属性的实际名称
        title_prop_name = self._get_title_property_name(db_properties)
        if not title_prop_name:
            raise NotionApiError(message="数据库中未找到标题属性")

        existing_map = {}
        next_cursor = None

        # 分页查询所有页面
        # 在 2025-09-03 API 版本中，如果数据库使用 data_sources，需要使用 data_source_id 查询
        query_endpoint = None
        if self._data_source_id:
            # 使用新API版本：通过 data_source_id 查询
            query_endpoint = f"/data_sources/{self._data_source_id}/query"
        else:
            # 使用旧API版本：通过 database_id 查询
            query_endpoint = f"/databases/{self._database_id}/query"

        while True:
            query_payload = {"page_size": 100}  # Notion API 最大页面大小
            if next_cursor:
                query_payload["start_cursor"] = next_cursor

            response = self._make_request("POST", query_endpoint, json=query_payload)
            data = response.json()

            # 提取游戏名称和页面ID
            for page in data.get("results", []):
                page_id = page.get("id")
                properties = page.get("properties", {})
                title_prop = properties.get(title_prop_name, {})
                title_array = title_prop.get("title", [])
                if title_array and page_id:
                    game_name = (
                        title_array[0].get("text", {}).get("content", "").strip()
                    )
                    if game_name:
                        existing_map[game_name] = page_id

            # 检查是否有更多页面
            next_cursor = data.get("next_cursor")
            if not next_cursor:
                break

        return existing_map

    @staticmethod
    def _parse_date(game: GameInfo) -> tp.Optional[str]:
        """
        解析游戏发布日期字符串为日期字符串 (YYYY-MM-DD)
        使用 dateparser 库支持多种语言和格式

        Args:
            game: 游戏信息对象

        Returns:
            str: 日期字符串 (YYYY-MM-DD) 或 None
        """
        # GameInfo.release_date 是字符串类型，直接使用
        date_str = game.release_date if game.release_date else None
        if not date_str:
            return None

        try:
            # dateparser 支持 200+ 种语言，自动识别语言和格式
            parsed_date = dateparser.parse(
                date_str,
                languages=None,  # 自动检测语言（支持 200+ 种语言）
                settings={
                    "PREFER_DAY_OF_MONTH": "first",  # 如果只有年月，使用月初
                    "PREFER_DATES_FROM": "past",  # 偏好过去的日期（适合游戏发布日期）
                    "RELATIVE_BASE": datetime.now(),  # 相对日期的基准
                },
            )

            if parsed_date:
                return parsed_date.strftime("%Y-%m-%d")
            else:
                echo.r(
                    f"游戏 '{game.name}:{game.id}' | 发布日期: '{date_str}' 无法解析"
                )
                return None
        except Exception as e:
            echo.r(f"游戏 '{game.name}:{game.id}' | 解析日期 '{date_str}' 时出错: {e}")
            return None

    def add_game(
        self,
        game: GameInfo,
        game_page: tp.Any = None,
        use_bg_as_cover: bool = False,
        skip_if_exists: bool = False,
        existing_names: tp.Optional[tp.Set[str]] = None,
    ) -> bool:
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
            raise NotionApiError(message="数据库ID未设置，请先创建或连接数据库")

        # 检查是否已存在
        if skip_if_exists:
            if existing_names is None:
                existing_names = self.get_existing_game_names()
            if game.name in existing_names:
                return True  # 已存在，跳过但不视为错误

        try:
            # 获取数据库属性（使用缓存或重新获取）
            db_properties = self._ensure_db_properties_cache()

            # 找到标题属性的实际名称
            title_prop_name = self._get_title_property_name(db_properties)
            if not title_prop_name:
                # 如果属性缓存为空，尝试重新获取
                if not db_properties:
                    echo.y("数据库属性为空，尝试重新获取...")
                    self._db_properties_cache = None
                    db_properties = self._ensure_db_properties_cache()
                    title_prop_name = self._get_title_property_name(db_properties)

                if not title_prop_name:
                    error_msg = "数据库中未找到标题属性"
                    echo.r(f"错误：{error_msg}")
                    echo.y(
                        "提示：Notion 数据库必须包含至少一个标题类型的属性才能添加页面。"
                    )
                    raise NotionApiError(message=error_msg)

            # 构建属性（包含标题）
            properties = self._build_game_properties(
                game, db_properties, include_title=True
            )

            # 构建请求体
            payload = {
                "parent": {"database_id": self._database_id},
                "properties": properties,
            }

            # 添加图标和封面
            payload.update(self._build_cover_payload(game, use_bg_as_cover))

            # 创建页面
            response = self._make_request("POST", "/pages", json=payload)
            # page_data = response.json()

            return True

        except Exception as e:
            echo.r(f"添加游戏 '{game.name}' 失败: {e}")
            return False

    def update_game(
        self,
        game: GameInfo,
        page_id: str,
        use_bg_as_cover: bool = False,
    ) -> bool:
        """
        更新Notion中已存在的游戏信息

        Args:
            game: 游戏信息对象
            page_id: 要更新的页面ID
            use_bg_as_cover: 是否使用背景图片作为封面

        Returns:
            bool: 是否更新成功
        """
        if not self._database_id:
            raise NotionApiError(message="数据库ID未设置，请先创建或连接数据库")

        try:
            # 获取数据库属性（使用缓存或重新获取）
            db_properties = self._ensure_db_properties_cache()

            # 构建属性（不包含标题）
            properties = self._build_game_properties(
                game, db_properties, include_title=False
            )

            # 构建请求体
            payload = {}

            # 如果有属性需要更新，添加到payload
            if properties:
                payload["properties"] = properties

            # 添加图标和封面
            payload.update(self._build_cover_payload(game, use_bg_as_cover))

            # 如果没有需要更新的内容，直接返回成功
            if not payload:
                return True

            # 更新页面
            response = self._make_request("PATCH", f"/pages/{page_id}", json=payload)

            return True

        except Exception as e:
            echo.r(f"更新游戏 '{game.name}' 失败: {e}")
            return False

    def import_game_list(
        self,
        game_list: tp.List[GameInfo],
        game_page: tp.Any = None,
        skip_duplicates: bool = True,
        update_mode: bool = False,
        **kwargs,
    ) -> tp.List[GameInfo]:
        """
        批量导入游戏列表到Notion

        Args:
            game_list: 游戏信息列表
            game_page: 兼容参数（新API中不需要）
            skip_duplicates: 是否跳过已存在的游戏（默认True，与update_mode互斥）
            update_mode: 是否更新已存在的游戏（默认False，与skip_duplicates互斥）
            **kwargs: 其他参数（如use_bg_as_cover）

        Returns:
            List[GameInfo]: 导入失败的游戏列表
        """
        errors = []
        skipped = []
        updated = []
        total = len(game_list)

        # 如果启用更新模式，skip_duplicates 应该为 False
        if update_mode:
            skip_duplicates = False

        # 如果需要去重或更新模式，先获取已有游戏信息
        # 注意：新建的数据库肯定是空的，不需要检查
        existing_names = None
        existing_map = None
        if skip_duplicates or update_mode:
            # 如果是新建的数据库，跳过检查（肯定是空的）
            if self._is_new_database:
                echo.y("新建数据库，跳过已有游戏检查")
                existing_names = set()  # 空集合，表示没有已有游戏
                existing_map = {}  # 空映射
            else:
                # 对于已有数据库，尝试获取已有游戏信息
                echo.y("正在查询已有游戏...")
                try:
                    if update_mode:
                        # 更新模式需要获取页面ID映射
                        existing_map = self.get_existing_game_map()
                        existing_names = set(existing_map.keys())
                        echo.g(f"数据库中已有 {len(existing_map)} 个游戏")
                    else:
                        # 普通模式只需要游戏名称集合
                        existing_names = self.get_existing_game_names()
                        echo.g(f"数据库中已有 {len(existing_names)} 个游戏")
                except NotionApiError as e:
                    # 如果是因为找不到标题属性而失败，给出更明确的提示
                    if "标题属性" in str(e):
                        echo.r(f"查询已有游戏失败: {e}，将继续导入但可能产生重复")
                        echo.y("提示：请确保数据库包含一个标题类型的属性")
                    else:
                        echo.r(f"查询已有游戏失败: {e}，将继续导入但可能产生重复")
                    skip_duplicates = False
                    update_mode = False
                    existing_names = None
                    existing_map = None
                except Exception as e:
                    echo.r(f"查询已有游戏失败: {e}，将继续导入但可能产生重复")
                    skip_duplicates = False
                    update_mode = False
                    existing_names = None
                    existing_map = None

        imported_count = 0
        skipped_count = 0
        updated_count = 0

        for i, game in enumerate(game_list, start=1):
            # 更新模式：如果游戏已存在，更新它
            if update_mode and existing_map and game.name in existing_map:
                page_id = existing_map[game.name]
                if self.update_game(game, page_id, **kwargs):
                    updated_count += 1
                    updated.append(game)
                    echo.c(
                        f"进度: {i}/{total} (已导入: {imported_count}, 已更新: {updated_count}, 已跳过: {skipped_count})",
                        end="\r",
                    )
                else:
                    errors.append(game)
                # 添加延迟以避免速率限制
                if i < total:
                    time.sleep(0.15)
                continue

            # 检查是否已存在（跳过模式）
            if skip_duplicates and existing_names and game.name in existing_names:
                skipped_count += 1
                skipped.append(game)
                echo.c(
                    f"进度: {i}/{total} (已导入: {imported_count}, 已跳过: {skipped_count})",
                    end="\r",
                )
                continue

            # 添加新游戏
            if self.add_game(
                game,
                game_page,
                skip_if_exists=skip_duplicates,
                existing_names=existing_names,
                **kwargs,
            ):
                imported_count += 1
                echo.c(
                    f"进度: {i}/{total} (已导入: {imported_count}, 已更新: {updated_count}, 已跳过: {skipped_count})",
                    end="\r",
                )
            else:
                errors.append(game)

            # 添加延迟以避免速率限制
            if i < total:
                time.sleep(0.3)

        echo.m("")  # 换行
        if skipped_count > 0:
            echo.y(f"已跳过 {skipped_count} 个已存在的游戏")
        if updated_count > 0:
            echo.g(f"已更新 {updated_count} 个已存在的游戏")

        return errors

    @staticmethod
    def _game_list_schema():
        """
        获取游戏列表数据库的属性架构定义（中文）

        Returns:
            dict: 数据库属性架构字典
        """
        return {
            "游戏名": {"title": {}},
            "状态": {
                "select": {
                    "options": [
                        {"name": "通关", "color": "green"},
                        {"name": "游玩中", "color": "yellow"},
                        {"name": "计划中", "color": "blue"},
                        {"name": "吃灰", "color": "gray"},
                        {"name": "弃坑", "color": "red"},
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
                        {"name": "Xbox", "color": "green"},
                    ]
                }
            },
            "发行日期": {"date": {}},
            "游戏时长(小时)": {"number": {"format": "number"}},
            "备注": {"rich_text": {}},
        }
