# Notion 游戏列表

将你的 Steam 游戏库自动导入到 Notion 数据库中，方便管理和追踪你的游戏收藏。

## ✨ 功能特性

- 🎮 **自动同步 Steam 游戏库**：从 Steam API 获取你的游戏列表
- 📊 **创建 Notion 数据库**：自动创建结构化的游戏数据库
- 🔄 **智能去重**：自动跳过已存在的游戏，支持追加导入
- 🖼️ **游戏封面和图标**：自动获取游戏封面、图标和背景图
- 📅 **发布日期**：自动获取并解析游戏发布日期（支持多种格式）
- ⏱️ **游戏时长**：显示你的游戏游玩时长
- ⚡ **缓存机制**：支持游戏信息缓存，加快重复导入速度
- 🎯 **灵活配置**：通过 `.env` 文件轻松配置所有选项

## 📋 环境要求

- Python 3.12+
- Notion Integration Token
- Steam API Key
- Steam 用户 ID

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 uv
uv sync
```

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env`，并填写你的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Notion 配置
NOTION_TOKEN=your_notion_token_here
NOTION_PAGE_ID=your_notion_page_id_here
# NOTION_DATABASE_ID=your_database_id_here  # 可选：连接到已有数据库

# Steam 配置
STEAM_TOKEN=your_steam_token_here
STEAM_USER=your_steam_user_id_here

# 导入选项
STORE_BG_COVER=false
SKIP_NON_STEAM=false
USE_ONLY_LIBRARY=false
SKIP_FREE_STEAM=false
STEAM_NO_CACHE=false
ALLOW_DUPLICATES=false

# 调试模式
DEBUG=false
```

### 3. 获取必要的凭证

#### Notion Integration Token

1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)
2. 创建新的 Integration
3. 复制 Integration Token 到 `NOTION_TOKEN`
4. 获取父页面 ID（从 Notion 页面 URL 中获取）到 `NOTION_PAGE_ID`

#### Steam API Key

1. 访问 [Steam API Key](https://steamcommunity.com/dev/apikey)
2. 注册并获取 API Key
3. 复制到 `STEAM_TOKEN`

#### Steam 用户 ID

- **数字 ID**：从 Steam 个人资料页面获取（如 `76561199077366346`）
- **自定义 URL**：你的 Steam 用户名（如 `your_username`）
- **完整 URL**：`https://steamcommunity.com/profiles/your_username`（会自动处理）

### 4. 运行程序

```bash
python main.py
```

## ⚙️ 配置选项说明

### Notion 配置

| 配置项 | 说明 | 必需 |
|--------|------|------|
| `NOTION_TOKEN` | Notion Integration Token | ✅ |
| `NOTION_PAGE_ID` | 父页面 ID（用于创建新数据库） | ⚠️* |
| `NOTION_DATABASE_ID` | 已有数据库 ID（连接到已有数据库） | ⚠️* |

*至少需要配置 `NOTION_PAGE_ID` 或 `NOTION_DATABASE_ID` 中的一个

### Steam 配置

| 配置项 | 说明 | 必需 |
|--------|------|------|
| `STEAM_TOKEN` | Steam API Key | ✅ |
| `STEAM_USER` | Steam 用户 ID（数字ID或用户名） | ✅ |

### 导入选项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `STORE_BG_COVER` | `false` | 使用 Steam 商店背景作为游戏封面 |
| `SKIP_NON_STEAM` | `false` | 跳过 Steam 商店中已下架的游戏 |
| `USE_ONLY_LIBRARY` | `false` | 仅从游戏库获取信息，不使用 Steam 商店 API |
| `SKIP_FREE_STEAM` | `false` | 跳过免费游戏（免费游玩） |
| `STEAM_NO_CACHE` | `false` | 不使用缓存的游戏信息 |
| `ALLOW_DUPLICATES` | `false` | 允许重复导入（默认会跳过已存在的游戏） |
| `TEST_LIMIT` | - | 测试模式：限制导入的游戏数量（可选） |
| `DEBUG` | `false` | 调试模式：开启后异常时会抛出完整堆栈信息 |

### 布尔值配置

所有布尔值选项支持以下格式：

- `true` / `false`
- `1` / `0`
- `yes` / `no`
- `on` / `off`

## 📖 使用场景

### 场景 1：创建新数据库

```env
NOTION_TOKEN=your_token
NOTION_PAGE_ID=your_page_id
STEAM_TOKEN=your_steam_token
STEAM_USER=your_user_id
```

程序会在指定的 Notion 页面中创建一个新的游戏数据库。

### 场景 2：追加到已有数据库

```env
NOTION_TOKEN=your_token
NOTION_DATABASE_ID=your_database_id
STEAM_TOKEN=your_steam_token
STEAM_USER=your_user_id
ALLOW_DUPLICATES=false  # 自动跳过已存在的游戏
```

程序会连接到已有数据库，只导入新游戏。

### 场景 3：快速导入（仅游戏库信息）

```env
USE_ONLY_LIBRARY=true
```

跳过 Steam 商店 API 调用，仅使用游戏库信息，速度更快但信息较少。

### 场景 4：跳过免费游戏

```env
SKIP_FREE_STEAM=true
```

只导入付费游戏，跳过免费游戏。

## 🔍 两种导入模式对比

### 模式 1：从 Steam 商店获取（默认）

**优点：**

- ✅ 信息完整（包含发布日期、是否免费等）
- ✅ 高清封面图
- ✅ 背景图片

**缺点：**

- ⚠️ 速度较慢
- ⚠️ 受速率限制（每5分钟200个游戏）
- ⚠️ 已下架游戏可能无法获取

### 模式 2：仅从游戏库获取（`USE_ONLY_LIBRARY=true`）

**优点：**

- ✅ 速度快
- ✅ 不受速率限制
- ✅ 可获取已下架游戏

**缺点：**

- ⚠️ 信息不完整（缺少发布日期等）
- ⚠️ 图片质量较低

## 📊 数据库结构

程序会自动创建包含以下属性的数据库：

- **游戏名** (Title) - 游戏名称
- **状态** (Select) - 通关、游玩中、计划中、吃灰、弃坑
- **平台** (Multi-select) - Steam、PC、Switch、PlayStation、Xbox
- **发行日期** (Date) - 游戏发布日期
- **游戏时长(小时)** (Number) - 你的游戏时长
- **备注** (Rich Text) - 额外信息

## 🛠️ 常见问题

### Q: 如何获取 Notion 页面 ID？

A: 从 Notion 页面 URL 中获取。URL 格式为：

```text
https://www.notion.so/Your-Page-Title-xxxxxxxxxxxxxxxxxxxxxxxx
```

其中 `xxxxxxxxxxxxxxxxxxxxxxxx` 就是页面 ID（32个字符，去掉连字符）。

### Q: 如何获取数据库 ID？

A: 打开数据库页面，URL 中的数据库 ID 就是 `NOTION_DATABASE_ID`。

### Q: 导入时出现"用户未找到"错误？

A: 检查 `STEAM_USER` 配置：

- 确保使用正确的数字 ID 或用户名
- 如果使用 URL，确保格式正确

### Q: 日期格式解析失败？

A: 程序支持多种日期格式，包括：

- 英语格式：`24 Feb, 2022`、`16. Nov. 2004`
- 俄语格式：`24 фев. 2022 г.`
- 如果仍有问题，请提交 Issue

### Q: 如何避免重复导入？

A: 默认情况下，程序会自动跳过已存在的游戏（按游戏名称判断）。如果需要强制重复导入，设置 `ALLOW_DUPLICATES=true`。

### Q: Steam 商店 API 速率限制？

A: Steam 商店 API 限制为每5分钟200个游戏。如果游戏库很大：

- 使用 `USE_ONLY_LIBRARY=true` 跳过商店 API

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📚 相关文档

- [Notion API 指南](NOTION_API_GUIDE.md)
- [迁移指南](MIGRATION_GUIDE.md)
