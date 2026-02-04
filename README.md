# 金融新闻获取系统

从多个国际和中文新闻源获取金融新闻，并发送到Telegram Bot。

## 项目结构
```
  finance_summary
  ├── 配置文件
  │   ├── config.py                    # 全局配置（代理、Telegram Bot令牌、API密钥）
  │   └── config/
  │       └── sources.yaml             # 新闻源配置文件（定义所有新闻网站URL和RSS）
  │
  ├── 核心模块
  │   ├── news_fetcher_v2.py           # 新闻抓取引擎（多策略抓取，7种重试方法）
  │   ├── ai_analyzer.py               # AI分析模块（调用智谱清言API分析新闻）
  │   └── send_finance_summary.py      # 主程序（抓取→分析→发送Telegram）
  │
  ├── 格式规范
  │   └── summary_finance.md           # 输出格式规范文档
  │
  ├── 测试和工具
  │   ├── test_sina.py                 # 新浪财经网站结构测试脚本
  │   └── setup_scheduled_tasks.bat    # Windows定时任务设置脚本
  │
  └── 其他
      └── .env                         # 环境变量（本地，未提交）
```
  
  文件作用
  ```
  ┌───────────────────────────┬───────────────────────────────────────────────────────────────────────────────┐
  │           文件            │                                     作用                                      │
  ├───────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
  │ news_fetcher_v2.py        │ 核心抓取引擎，支持RSS、BeautifulSoup、Requests多种方式，每个源最多尝试7种方法 │
  ├───────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
  │ ai_analyzer.py            │ 调用智谱清言GLM-4-Flash API生成新闻总结和重要消息分析                         │
  ├───────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
  │ send_finance_summary.py   │ 主程序：调用fetcher抓取新闻→调用analyzer分析→每10条合并发送到Telegram         │
  ├───────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
  │ config/sources.yaml       │ 定义12个新闻源（新浪财经、东方财富、CNBC、Yahoo等）的URL和RSS feeds           │
  ├───────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
  │ config.py                 │ 代理配置、Telegram Bot令牌、聊天ID                                            │
  ├───────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
  │ summary_finance.md        │ 定义输出格式：【来源】#标题 + 【总结】板块 + 【重要消息】板块                 │
  ├───────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
  │ setup_scheduled_tasks.bat │ 设置Windows定时任务，每天8:00和18:00自动运行                                  │
  └───────────────────────────┴───────────────────────────────────────────────────────────────────────────────┘
  ```

  数据流程


  ```
  sources.yaml → news_fetcher_v2.py → 文章
       ↓                              ↓
  send_finance_summary.py → ai_analyzer.py → AI分析
       ↓                              ↓
     格式化 → Telegram Bot → 用户接收
```


----------------------------------------------------------------------------------------------------------------
## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
# Telegram Bot配置
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here

# 代理配置（可选）
PROXY_HOST=127.0.0.1
PROXY_PORT=7897
```

### 3. 使用

#### 方法1: Telegram Bot命令 ⭐ 推荐

在Telegram聊天框中直接发送命令：

```
/news          - 获取新闻摘要
/news5         - 获取5篇新闻
/sina          - 获取新浪新闻
/search AI     - 搜索关键词
/help          - 查看帮助
```

#### 方法2: 命令行

```python
# 【正式测试】与telegram bot 发送消息一致 （推荐使用，因为其他的我还没测试）
python send_finance_summary.py

# 测试1条新闻
python telegram_news_bot.py --test

# 获取新闻
python telegram_news_bot.py --cmd '/news'

# 搜索新闻
python telegram_news_bot.py --cmd '/search AI'
```

## 核心文件

| 文件 | 说明 |
|------|------|
| `telegram_news_bot.py` | Telegram Bot - 主要使用方式 |
| `news_fetcher_v2.py` | 新闻抓取器（支持5种重试方法） |
| `openclaw_news_skill.py` | OpenClaw Skill接口 （正在开发）|
| `config/sources.yaml` | 新闻源配置（25个源） |
| `config.py` | 配置管理 |

## 支持的新闻源

### 国际媒体（12个）
Reuters, Bloomberg, CNBC, Yahoo Finance, The Verge, Ars Technica, NVIDIA, AI News, MarketWatch, Seeking Alpha, TechCrunch, WSJ中文

### 中国媒体（13个）
新浪财经、东方财富、雪球、证券时报、中国证券报、第一财经、财新、网易财经、腾讯财经、搜狐财经、金融界

## 功能特性

- ✅ 5种智能重试机制
- ✅ 成功方法自动保存
- ✅ 英文新闻自动翻译
- ✅ Telegram Bot集成
- ✅ 关键词搜索
- ✅ 用户偏好管理 （正在开发）

## 文档

- [Telegram Bot使用指南](TELEGRAM_BOT_GUIDE.md)
- [OpenClaw Skill文档](OPENCLAW_SKILL_README.md)
- [实现总结](IMPLEMENTATION_SUMMARY.md)

## 依赖

```
requests
beautifulsoup4
lxml
pyyaml
python-dotenv
```

## 测试

```python
# 【正式测试】与telegram bot 发送消息一致
python send_finance_summary.py

# 测试1条新闻
python telegram_news_bot.py --test

# 测试OpenClaw Skill
python openclaw_news_skill.py
```
