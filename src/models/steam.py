"""
Steam数据模型
定义Steam商店API返回的数据结构
"""

import typing as tp

from src.models.base import BaseModel


class SteamStoreAppPriceOverview(BaseModel):
    """
    Steam商店应用价格概览模型
    包含游戏的价格信息，如原价、现价、折扣等
    """

    def __init__(
        self,
        currency: str,
        initial: int,
        final: int,
        discount_percent: int,
        initial_formatted: str,
        final_formatted: str,
        **kwargs,
    ):
        """
        初始化价格概览

        Args:
            currency: 货币代码
            initial: 原价（分）
            final: 现价（分）
            discount_percent: 折扣百分比
            initial_formatted: 格式化后的原价字符串
            final_formatted: 格式化后的现价字符串
            **kwargs: 其他未使用的参数
        """
        self.currency = currency
        self.initial = initial
        self.final = final
        self.discount_percent = discount_percent
        self.initial_formatted = initial_formatted
        self.final_formatted = final_formatted


class SteamStoreAppPackageGroupSub(BaseModel):
    """
    Steam商店应用包组子项模型
    表示游戏包中的一个子选项
    """

    def __init__(
        self,
        packageid: int,
        percent_savings_text: str,
        percent_savings: int,
        option_text: str,
        option_description: str,
        can_get_free_license: str,
        is_free_license: bool,
        price_in_cents_with_discount: int,
        **kwargs,
    ):
        """
        初始化包组子项

        Args:
            packageid: 包ID
            percent_savings_text: 节省百分比文本
            percent_savings: 节省百分比
            option_text: 选项文本
            option_description: 选项描述
            can_get_free_license: 是否可以免费获取许可证
            is_free_license: 是否为免费许可证
            price_in_cents_with_discount: 折扣后价格（分）
            **kwargs: 其他未使用的参数
        """
        self.packageid = packageid
        self.percent_savings_text = percent_savings_text
        self.percent_savings = percent_savings
        self.option_text = option_text
        self.option_description = option_description
        self.can_get_free_license = can_get_free_license
        self.is_free_license = is_free_license
        self.price_in_cents_with_discount = price_in_cents_with_discount


class SteamStoreAppPackageGroup(BaseModel):
    """
    Steam商店应用包组模型
    表示游戏的不同购买包组合
    """

    def __init__(
        self,
        name: str,
        title: str,
        description: str,
        selection_text: str,
        save_text: str,
        display_type: int,
        is_recurring_subscription: str,
        subs: tp.List[SteamStoreAppPackageGroupSub],
    ):
        """
        初始化包组

        Args:
            name: 包组名称
            title: 包组标题
            description: 包组描述
            selection_text: 选择文本
            save_text: 保存文本
            display_type: 显示类型
            is_recurring_subscription: 是否为定期订阅
            subs: 子项列表
        """
        self.name = name
        self.title = title
        self.description = description
        self.selection_text = selection_text
        self.save_text = save_text
        self.display_type = display_type
        self.is_recurring_subscription = is_recurring_subscription
        self.subs = subs

    @classmethod
    def load(cls, d: tp.Optional[dict]):
        """
        从字典加载包组对象，递归加载子项

        Args:
            d: 包含包组数据的字典

        Returns:
            SteamStoreAppPackageGroup实例或None
        """
        if d is None:
            return None
        d["subs"] = [SteamStoreAppPackageGroupSub.load(t) for t in d["subs"]]
        return cls(**d)


class SteamStoreAppCategory(BaseModel):
    """
    Steam商店应用分类模型
    表示游戏的分类信息
    """

    def __init__(self, id: int, description: str, **kwargs):
        """
        初始化分类

        Args:
            id: 分类ID
            description: 分类描述
            **kwargs: 其他未使用的参数
        """
        self.id = id
        self.description = description


class SteamStoreAppGenre(BaseModel):
    """
    Steam商店应用类型模型
    表示游戏的类型/流派
    """

    def __init__(self, id: str, description: str, **kwargs):
        """
        初始化类型

        Args:
            id: 类型ID
            description: 类型描述
            **kwargs: 其他未使用的参数
        """
        self.id = id
        self.description = description


class SteamStoreAppScreenshot(BaseModel):
    """
    Steam商店应用截图模型
    表示游戏的截图信息
    """

    def __init__(self, id: int, path_thumbnail: str, path_full: str, **kwargs):
        """
        初始化截图

        Args:
            id: 截图ID
            path_thumbnail: 缩略图路径
            path_full: 完整图片路径
            **kwargs: 其他未使用的参数
        """
        self.id = id
        self.path_thumbnail = path_thumbnail
        self.path_full = path_full


class SteamStoreAppMovie(BaseModel):
    """
    Steam商店应用视频模型
    表示游戏的宣传视频信息
    """

    def __init__(
        self,
        id: int,
        name: str,
        thumbnail: str,
        webm: tp.Optional[tp.Dict[str, str]] = None,
        mp4: tp.Optional[tp.Dict[str, str]] = None,
        highlight: bool = False,
        **kwargs,
    ):
        """
        初始化视频

        Args:
            id: 视频ID
            name: 视频名称
            thumbnail: 缩略图URL
            webm: WebM格式视频URL字典
            mp4: MP4格式视频URL字典
            highlight: 是否为高亮视频
            **kwargs: 其他未使用的参数
        """
        self.id = id
        self.name = name
        self.thumbnail = thumbnail
        self.webm = webm or {}
        self.mp4 = mp4 or {}
        self.highlight = highlight


class SteamStoreAppMetacriticScore(BaseModel):
    """
    Steam商店应用Metacritic评分模型
    表示游戏的Metacritic评分信息
    """

    def __init__(self, score: int, url: tp.Optional[str] = None, **kwargs):
        """
        初始化Metacritic评分

        Args:
            score: 评分分数
            url: 评分页面URL（可选）
            **kwargs: 其他未使用的参数
        """
        self.score = score
        self.url = url


class SteamStoreAppAchievementHighlighted(BaseModel):
    """
    Steam商店应用高亮成就模型
    表示游戏的高亮成就信息
    """

    def __init__(self, name: str, path: str, **kwargs):
        """
        初始化高亮成就

        Args:
            name: 成就名称
            path: 成就图标路径
            **kwargs: 其他未使用的参数
        """
        self.name = name
        self.path = path


class SteamStoreAppAchievements(BaseModel):
    """
    Steam商店应用成就模型
    表示游戏的成就信息
    """

    def __init__(
        self,
        total: int,
        highlighted: tp.List[SteamStoreAppAchievementHighlighted],
        **kwargs,
    ):
        """
        初始化成就

        Args:
            total: 总成就数
            highlighted: 高亮成就列表
            **kwargs: 其他未使用的参数
        """
        self.total = total
        self.highlighted = highlighted

    @classmethod
    def load(cls, d: tp.Optional[dict]):
        """
        从字典加载成就对象，递归加载高亮成就

        Args:
            d: 包含成就数据的字典

        Returns:
            SteamStoreAppAchievements实例或None
        """
        if d is None:
            return None
        d["highlighted"] = [
            SteamStoreAppAchievementHighlighted.load(t)
            for t in d.get("highlighted", [])
        ]
        return cls(**d)


class SteamStoreAppReleaseDate(BaseModel):
    """
    Steam商店应用发布日期模型
    表示游戏的发布日期信息
    """

    def __init__(self, coming_soon: bool, date: str, **kwargs):
        """
        初始化发布日期

        Args:
            coming_soon: 是否即将发布
            date: 发布日期字符串
            **kwargs: 其他未使用的参数
        """
        self.coming_soon = coming_soon
        self.date = date if date else None


class SteamStoreAppSupportInfo(BaseModel):
    """
    Steam商店应用支持信息模型
    表示游戏的支持联系方式
    """

    def __init__(self, url: str, email: str, **kwargs):
        """
        初始化支持信息

        Args:
            url: 支持页面URL
            email: 支持邮箱
            **kwargs: 其他未使用的参数
        """
        self.url = url
        self.email = email


class SteamStoreAppContentDescriptors(BaseModel):
    """
    Steam商店应用内容描述符模型
    表示游戏的内容分级信息
    """

    def __init__(self, ids: tp.List[int], notes: str, **kwargs):
        """
        初始化内容描述符

        Args:
            ids: 内容描述符ID列表
            notes: 备注说明
            **kwargs: 其他未使用的参数
        """
        self.ids = ids
        self.notes = notes


class SteamStoreApp(BaseModel):
    """
    Steam商店应用主模型
    包含游戏的所有详细信息
    """

    def __init__(
        self,
        type: str,
        name: str,
        steam_appid: int,
        required_age: tp.Union[str, int],
        is_free: bool,
        detailed_description: str,
        about_the_game: str,
        short_description: str,
        header_image: str,
        publishers: tp.List[str],
        platforms: tp.Dict[str, bool],
        release_date: SteamStoreAppReleaseDate,
        support_info: SteamStoreAppSupportInfo,
        package_groups: tp.List[SteamStoreAppPackageGroup],
        background: str,
        content_descriptors: tp.Optional[SteamStoreAppContentDescriptors] = None,
        screenshots: tp.Optional[tp.List[SteamStoreAppScreenshot]] = None,
        categories: tp.Optional[tp.List[SteamStoreAppCategory]] = None,
        developers: tp.Optional[tp.List[str]] = None,
        supported_languages: tp.Optional[str] = None,
        recommendations: tp.Optional[tp.Dict[str, int]] = None,
        genres: tp.Optional[tp.List[SteamStoreAppGenre]] = None,
        packages: tp.Optional[tp.List[int]] = None,
        achievements: tp.Optional[SteamStoreAppAchievements] = None,
        metacritic: tp.Optional[SteamStoreAppMetacriticScore] = None,
        movies: tp.Optional[tp.List[SteamStoreAppMovie]] = None,
        price_overview: tp.Optional[SteamStoreAppPriceOverview] = None,
        reviews: tp.Optional[str] = None,
        legal_notice: tp.Optional[str] = None,
        demos: tp.Optional[tp.List[dict]] = None,
        dlc: tp.Optional[tp.List[int]] = None,
        website: tp.Optional[str] = None,
        pc_requirements: tp.Dict[str, str] = None,
        mac_requirements: tp.Dict[str, str] = None,
        linux_requirements: tp.Dict[str, str] = None,
        **kwargs,
    ):
        """
        初始化Steam商店应用对象

        Args:
            type: 应用类型（如"game"）
            name: 游戏名称
            steam_appid: Steam应用ID
            required_age: 年龄限制
            is_free: 是否为免费游戏
            detailed_description: 详细描述
            about_the_game: 关于游戏
            short_description: 简短描述
            header_image: 头部图片URL
            publishers: 发行商列表
            platforms: 支持的平台字典
            release_date: 发布日期对象
            support_info: 支持信息对象
            package_groups: 包组列表
            background: 背景图片URL
            content_descriptors: 内容描述符（可选）
            screenshots: 截图列表（可选）
            categories: 分类列表（可选）
            developers: 开发商列表（可选）
            supported_languages: 支持的语言（可选）
            recommendations: 推荐数（可选）
            genres: 类型列表（可选）
            packages: 包ID列表（可选）
            achievements: 成就信息（可选）
            metacritic: Metacritic评分（可选）
            movies: 视频列表（可选）
            price_overview: 价格概览（可选）
            reviews: 评论摘要（可选）
            legal_notice: 法律声明（可选）
            demos: 演示版列表（可选）
            dlc: DLC ID列表（可选）
            website: 官方网站（可选）
            pc_requirements: PC系统需求（可选）
            mac_requirements: Mac系统需求（可选）
            linux_requirements: Linux系统需求（可选）
            **kwargs: 其他未使用的参数
        """
        self.type = type
        self.name = name
        self.steam_appid = steam_appid
        self.required_age = required_age
        self.is_free = is_free
        self.detailed_description = detailed_description
        self.about_the_game = about_the_game
        self.short_description = short_description
        self.supported_languages = supported_languages
        self.header_image = header_image
        self.developers = developers
        self.publishers = publishers
        self.packages = packages
        self.platforms = platforms
        self.metacritic = metacritic
        self.categories = categories
        self.genres = genres
        self.screenshots = screenshots
        self.movies = movies
        self.recommendations = recommendations
        self.achievements = achievements
        self.release_date = release_date
        self.support_info = support_info
        self.package_groups = package_groups
        self.background = background
        self.content_descriptors = content_descriptors
        self.price_overview = price_overview
        self.reviews = reviews
        self.legal_notice = legal_notice
        self.demos = demos
        self.dlc = dlc
        self.website = website
        self.pc_requirements = pc_requirements
        self.mac_requirements = mac_requirements
        self.linux_requirements = linux_requirements

    @classmethod
    def load(cls, d: tp.Optional[dict]):
        """
        从字典加载Steam商店应用对象
        递归加载所有嵌套的对象和列表

        Args:
            d: 包含应用数据的字典

        Returns:
            SteamStoreApp实例或None
        """
        if d is None:
            return None
        try:
            # 检查必需字段是否存在
            required_fields = ["release_date", "support_info", "package_groups"]
            for field in required_fields:
                if field not in d:
                    logger.warning(f"SteamStoreApp 缺少必需字段: {field}")
                    return None

            # 递归加载所有嵌套对象
            d["release_date"] = SteamStoreAppReleaseDate.load(d["release_date"])
            d["support_info"] = SteamStoreAppSupportInfo.load(d["support_info"])
            d["package_groups"] = [
                SteamStoreAppPackageGroup.load(t) for t in d["package_groups"]
            ]
            d["content_descriptors"] = SteamStoreAppContentDescriptors.load(
                d.get("content_descriptors")
            )
            d["screenshots"] = [
                SteamStoreAppScreenshot.load(t) for t in d.get("screenshots", [])
            ]
            d["categories"] = [
                SteamStoreAppCategory.load(t) for t in d.get("categories", [])
            ]
            d["genres"] = [SteamStoreAppGenre.load(t) for t in d.get("genres", [])]
            d["achievements"] = SteamStoreAppAchievements.load(d.get("achievements"))
            d["metacritic"] = SteamStoreAppMetacriticScore.load(d.get("metacritic"))
            d["movies"] = [SteamStoreAppMovie.load(t) for t in d.get("movies", [])]
            d["price_overview"] = SteamStoreAppPriceOverview.load(
                d.get("price_overview")
            )
            return cls(**d)
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(f"加载 SteamStoreApp 失败: {e}")
            return None
