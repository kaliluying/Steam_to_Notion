# Steam_To_Notion

将你的 Steam 游戏库自动导入到 Notion 数据库中，方便管理和追踪你的游戏收藏。基于 [notion-game-list](https://github.com/solesensei/notion-game-list) 二次开发优化。

## ✨ 功能特性

- 🎮 自动同步 Steam 游戏库
- 📊 自动创建/更新 Notion 数据库
- 🔄 智能去重，支持追加导入和更新模式
- 🖼️ 自动获取游戏封面、图标和背景图
- 📅 智能日期解析：使用 dateparser 支持 200+ 种语言的日期格式
- ⏱️ 显示游戏游玩时长
- ⚡ 缓存机制，加快重复导入速度

## 📋 环境要求

- Python 3.12+
- Notion Integration Token
- Steam API Key
- Steam 用户 ID

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或使用 uv sync
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```env
# Notion 配置
NOTION_TOKEN=your_notion_token_here
NOTION_PAGE_ID=your_notion_page_id_here  # 或使用 NOTION_DATABASE_ID 连接已有数据库

# Steam 配置
STEAM_TOKEN=your_steam_token_here
STEAM_USER=your_steam_user_id_here

# 导入选项（可选）
STEAM_CACHE=true
UPDATE_MODE=false  # 更新模式：更新已存在的游戏信息
TEST_LIMIT=10  # 测试模式：限制导入数量
```

### 3. 获取凭证

- **Notion Token**: 访问 [Notion Integrations](https://www.notion.so/my-integrations) 创建 Integration
- **Notion Page/Database ID**: 从页面 URL 中获取（32 位字符，去掉连字符）

![image-20251118170958903](https://gmlblog.oss-cn-hangzhou.aliyuncs.com/img/
image-20251118170958903.png)

- **Steam API Key**: 访问 [Steam API Key](https://steamcommunity.com/dev/apikey) 获取
- **Steam User ID**: 数字 ID 或用户名（支持完整 URL，会自动处理）

### 4. 运行程序

```bash
python main.py
```

![image-20251118171155124](https://gmlblog.oss-cn-hangzhou.aliyuncs.com/img/
image-20251118171155124.png)

## ⚙️ 配置选项

### 必需配置

| 配置项                                   | 说明                              |
| ---------------------------------------- | --------------------------------- |
| `NOTION_TOKEN`                           | Notion Integration Token          |
| `NOTION_PAGE_ID` 或 `NOTION_DATABASE_ID` | 至少配置一个                      |
| `STEAM_TOKEN`                            | Steam API Key                     |
| `STEAM_USER`                             | Steam 用户 ID（数字 ID 或用户名） |

### 可选配置

| 配置项             | 默认值  | 说明                                     |
| ------------------ | ------- | ---------------------------------------- |
| `STORE_BG_COVER`   | `false` | 使用 Steam 商店背景作为封面              |
| `SKIP_NON_STEAM`   | `false` | 跳过 Steam 商店中已下架的游戏            |
| `USE_ONLY_LIBRARY` | `false` | 仅从游戏库获取信息（速度快，但信息较少） |
| `SKIP_FREE_STEAM`  | `false` | 跳过免费游戏                             |
| `STEAM_CACHE`      | `true`  | 使用缓存加快重复导入                     |
| `UPDATE_MODE`      | `false` | 更新模式：更新已存在的游戏信息（而非跳过） |
| `TEST_LIMIT`       | -       | 测试模式：限制导入数量                   |
| `DEBUG`            | `false` | 调试模式                                 |

布尔值支持：`true`/`false`、`1`/`0`、`yes`/`no`、`on`/`off`

## 📖 使用说明

### 运行流程

1. 验证配置 → 2. 登录 Notion → 3. 登录 Steam → 4. 获取游戏列表 → 5. 创建/连接数据库 → 6. 导入游戏

### 数据库结构

自动创建包含以下属性的数据库：

- **游戏名** (Title)
- **状态** (Select): 通关、游玩中、计划中、吃灰、弃坑
- **平台** (Multi-select): Steam、PC、Switch、PlayStation、Xbox
- **发行日期** (Date)
- **游戏时长(小时)** (Number)
- **备注** (Rich Text)

### 使用场景

**创建新数据库：**

```env
NOTION_PAGE_ID=your_page_id
```

**追加到已有数据库：**

```env
NOTION_DATABASE_ID=your_database_id
# 默认自动跳过已存在的游戏
```

**更新已存在的游戏信息：**

```env
NOTION_DATABASE_ID=your_database_id
UPDATE_MODE=true  # 更新已存在的游戏信息（封面、时长等）
```

**快速导入（仅游戏库信息）：**

```env
USE_ONLY_LIBRARY=true  # 跳过商店 API，速度快但信息较少
```

**测试模式：**

```env
TEST_LIMIT=10  # 只导入前 10 个游戏
```

### 导入模式对比

| 模式                                          | 优点                       | 缺点                                     |
| --------------------------------------------- | -------------------------- | ---------------------------------------- |
| **从 Steam 商店获取**（默认）                 | 信息完整、高清封面、背景图 | 速度较慢、受速率限制（每 5 分钟 200 个） |
| **仅从游戏库获取**（`USE_ONLY_LIBRARY=true`） | 速度快、不受限制           | 信息不完整、图片质量较低                 |

### 缓存机制

- **启用缓存**（默认）：首次运行获取所有信息并缓存，后续运行只获取新游戏
- **禁用缓存**：每次运行都重新获取，确保信息最新但速度较慢

缓存文件：`game_info_cache.json`

## 🛠️ 常见问题

**Q: 如何获取 Notion 页面/数据库 ID？**  
A: 从页面 URL 中获取，格式：`https://www.notion.so/...-xxxxxxxxxxxxxxxxxxxxxxxx`（32 位字符，去掉连字符）

**Q: 如何避免重复导入？**  
A: 默认自动跳过已存在的游戏。如果需要更新已存在游戏的信息（如封面、时长等），设置 `UPDATE_MODE=true` 即可更新，而不会创建重复条目

**Q: Steam 商店 API 速率限制？**  
A: 每 5 分钟 200 个游戏，游戏库很大时使用 `USE_ONLY_LIBRARY=true` 跳过商店 API

**Q: 日期格式解析失败？**  
A: 使用 `dateparser` 库自动识别和解析 200+ 种语言的日期格式（包括英语、俄语、中文、日语等）。如果仍有问题请提交 Issue

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

**版权信息：**

- 原始项目：Copyright (c) 2020 solesensei ([notion-game-list](https://github.com/solesensei/notion-game-list))
- 当前版本：Copyright (c) 2025 kaliluying ([Steam_to_Notion](https://github.com/kaliluying/Steam_to_Notion))

### 主要优化/修改

- 🔄 **迁移至官方 Notion API**：基于官方 Notion REST API (2025-09-03)
- 📊 **支持更新现有数据库**：可直接连接到已有数据库并追加新游戏
- 🔄 **更新模式**：支持更新已存在游戏的信息（封面、时长等），而不会创建重复条目
- 📅 **智能日期解析**：使用 dateparser 库自动识别和解析 200+ 种语言的日期格式（包括英语、俄语、中文、日语等）

## 🙏 致谢

感谢原始项目作者 [solesensei](https://github.com/solesensei) 的开源贡献。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
