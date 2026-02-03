# OpenClaw News Skill 使用文档

## 概述

已成功将金融新闻获取项目封装为OpenClaw Skill，可通过OpenClaw调用获取金融新闻。

## 文件说明

### 核心文件

1. **`openclaw_news_skill.py`** - OpenClaw Skill主文件
   - 提供OpenClaw可调用的接口函数
   - 支持用户偏好管理
   - 集成Telegram发送功能

2. **`news_fetcher_v2.py`** - 通用新闻抓取器V2
   - 支持所有配置的新闻源
   - 5次智能重试机制
   - 成功方法自动保存
   - 移除了feedparser依赖

3. **`config/sources.yaml`** - 新闻源配置
   - 配置了23个新闻源
   - 包括国际和中英文媒体

### 数据文件

- **`data/success_methods.json`** - 成功的抓取方法记录
- **`data/user_preferences.json`** - 用户偏好设置（自动生成）

## OpenClaw调用接口

### 1. 获取新闻摘要

```python
from openclaw_news_skill import fetch_news_summary

# 获取所有源的新闻摘要（每个源最多5篇）
result = fetch_news_summary(max_articles=5)

# 只获取特定源的新闻
result = fetch_news_summary(max_articles=3, sources=['sina_finance', 'reuters'])
```

**返回示例：**
```
抓取完成！
成功源: 15/23
总文章数: 45

[sina_finance]
  - 央行发布最新金融政策...
  - 股市今日表现...

[reuters]
  - Tech stocks rally...
```

### 2. 获取并发送到Telegram

```python
from openclaw_news_skill import send_news_to_telegram

# 获取新闻并发送到Telegram
result = send_news_to_telegram(max_articles=5, send=True)
```

**返回示例：**
```
抓取完成！
成功源: 15/23
总文章数: 45

[SUCCESS] 已发送到Telegram!
```

### 3. 关键词搜索

```python
from openclaw_news_skill import search_news

# 搜索关键词相关新闻
result = search_news(keyword="AI", max_articles=10)
```

**返回示例：**
```
关键词搜索: AI
找到 8 篇相关文章

1. OpenAI发布新模型
   来源: techcrunch
   链接: https://techcrunch.com/...

2. AI芯片需求激增
   来源: arstechnica
   链接: https://arstechnica.com/...
```

## 用户偏好管理

### 设置偏好

```python
from openclaw_news_skill import OpenClawNewsSkill

skill = OpenClawNewsSkill()

# 设置偏好的新闻源
skill.set_preference('preferred_sources', ['sina_finance', 'bloomberg'])

# 设置关注的关键词
skill.set_preference('keywords', ['AI', 'crypto', '股票'])

# 设置语言偏好
skill.set_preference('language', 'zh')

# 设置每次获取的最大文章数
skill.set_preference('max_articles', 10)
```

### 获取偏好

```python
# 获取偏好的新闻源
sources = skill.get_preference('preferred_sources', [])

# 获取关注的关键词
keywords = skill.get_preference('keywords', [])
```

## 测试

### 快速测试（1条新闻）

```bash
python openclaw_news_skill.py
```

这将：
1. 从sina_finance获取1条新闻
2. 发送到您的Telegram Bot
3. 显示测试结果

### 完整测试（所有源）

```bash
python news_fetcher_v2.py
```

这将：
1. 尝试从所有23个启用的新闻源获取新闻
2. 每个源最多5篇文章
3. 保存成功的方法到`data/success_methods.json`
4. 保存所有新闻到JSON文件

## 新闻源列表

### 国际媒体（12个）
- Reuters (路透社)
- WSJ Chinese (华尔街见闻中文)
- Bloomberg (彭博社)
- CNBC
- Yahoo Finance
- The Verge
- Ars Technica
- NVIDIA News
- AI News
- MarketWatch
- Seeking Alpha
- TechCrunch

### 中国媒体（11个）
- 新浪财经
- 东方财富网
- 雪球网
- 证券时报
- 中国证券报
- 第一财经
- 财新网
- 网易财经
- 腾讯财经
- 搜狐财经
- 金融界

### 测试结果

根据最近的测试：
- **成功源**: 8个
- **失败源**: 15个
- **成功率**: 约35%

成功的源包括：
- cnbc (RSS)
- yahoo_finance (RSS)
- arstechnica (RSS)
- nvidia_news (RSS)
- techcrunch (RSS)
- yicai (通用抓取)
- jrj (通用抓取)
- sina_finance (通用抓取)

## 重试机制

每个新闻源都会尝试5种不同的方法：

1. **方法1**: BeautifulSoup XML解析RSS
2. **方法2**: 直接HTTP请求RSS
3. **方法3-4**: 不同User-Agent请求RSS
4. **方法5**: 通用方法（首页抓取）

成功的方法会被保存，下次直接使用该方法。

## 与OpenClaw集成

### 示例1：对话中获取新闻

```
用户: 给我最新的金融新闻摘要
OpenClaw: [调用 fetch_news_summary()]
[返回新闻摘要]
```

### 示例2：定时发送到Telegram

```
用户: 每天早上8点发送新闻到我的Telegram
OpenClaw: [设置定时任务调用 send_news_to_telegram()]
[任务已设置]
```

### 示例3：个性化新闻推荐

```
用户: 我关注AI和加密货币新闻
OpenClaw: [skill.set_preference('keywords', ['AI', 'crypto'])]
用户: 推荐相关新闻
OpenClaw: [根据偏好筛选新闻]
```

## 配置文件

### `.env` - 环境变量

```env
# Telegram Bot配置
BOT_TOKEN=your_bot_token
CHAT_ID=your_chat_id

# 代理配置
PROXY_HOST=127.0.0.1
PROXY_PORT=7897
```

### `config/sources.yaml` - 新闻源配置

可以添加、删除或禁用新闻源：

```yaml
sources:
  custom_source:
    name: "自定义源"
    enabled: true
    url: "https://example.com"
    rss_feeds:
      - "https://example.com/rss.xml"
    type: "rss"
```

## 故障排除

### 问题1：无法获取新闻

**解决方案：**
1. 检查网络连接
2. 检查代理配置
3. 查看成功方法文件是否被保存

### 问题2：RSS源403/401错误

**解决方案：**
- 系统会自动尝试通用方法（网页抓取）
- 检查`data/success_methods.json`查看哪种方法有效

### 问题3：Telegram发送失败

**解决方案：**
1. 检查`.env`文件中的BOT_TOKEN和CHAT_ID
2. 检查代理配置
3. 尝试手动测试：`python simple_news_test.py`

## 性能优化

### 成功方法缓存

系统会自动保存每个源的成功方法：
- 首次抓取会尝试5种方法
- 成功后保存方法
- 下次直接使用已知方法

### 并发抓取

可以修改代码实现并发抓取以提高速度：
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetcher.fetch_with_retries, ...) for ...]
```

## 总结

现在您可以：

1. ✅ 在OpenClaw对话中获取金融新闻
2. ✅ 设置定时任务自动发送到Telegram
3. ✅ 根据用户偏好个性化推荐
4. ✅ 搜索特定关键词的新闻
5. ✅ 管理用户偏好和设置

该Skill已通过测试，成功获取1条新闻并发送到Telegram。
