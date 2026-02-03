# -*- coding: utf-8 -*-
"""
OpenClaw News Skill
金融新闻获取Skill - 可被OpenClaw调用
"""
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

# 导入新闻抓取器
from news_fetcher_v2 import NewsFetcher
from config import PROXIES, BOT_TOKEN, CHAT_ID

class OpenClawNewsSkill:
    """OpenClaw新闻Skill"""

    def __init__(self):
        self.fetcher = NewsFetcher()
        self.user_preferences_file = Path(__file__).parent / 'data' / 'user_preferences.json'
        self.user_preferences = self.load_user_preferences()

    def load_user_preferences(self) -> Dict:
        """加载用户偏好"""
        if self.user_preferences_file.exists():
            try:
                with open(self.user_preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'preferred_sources': [],  # 用户偏好的新闻源
            'keywords': [],            # 关注的关键词
            'language': 'zh',          # 语言偏好
            'max_articles': 5          # 每次获取的最大文章数
        }

    def save_user_preferences(self):
        """保存用户偏好"""
        data_dir = Path(__file__).parent / 'data'
        data_dir.mkdir(exist_ok=True)

        with open(self.user_preferences_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)

    def get_news_summary(self, max_articles: int = 5, sources: Optional[List[str]] = None) -> Dict:
        """
        获取新闻摘要

        Args:
            max_articles: 每个源最多获取的文章数（默认5）
            sources: 指定新闻源列表（None表示使用所有启用的源）

        Returns:
            包含新闻数据和统计信息的字典
        """
        # 获取新闻
        if sources:
            # 只获取指定源的新闻
            all_articles = {}
            for source_name in sources:
                if source_name in self.fetcher.sources:
                    source_config = self.fetcher.sources[source_name]
                    if source_config.get('enabled', False):
                        articles = self.fetcher.fetch_with_retries(
                            source_name, source_config, max_articles
                        )
                        all_articles[source_name] = articles
        else:
            # 获取所有源的新闻
            all_articles = self.fetcher.fetch_all_sources(max_articles)

        # 统计
        total_articles = sum(len(articles) for articles in all_articles.values())
        successful_sources = sum(1 for articles in all_articles.values() if articles)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_sources': len(all_articles),
            'successful_sources': successful_sources,
            'total_articles': total_articles,
            'articles': all_articles
        }

    def get_news_by_keyword(self, keyword: str, max_articles: int = 10) -> List[Dict]:
        """
        根据关键词获取新闻

        Args:
            keyword: 搜索关键词
            max_articles: 最大文章数

        Returns:
            匹配的文章列表
        """
        result = self.get_news_summary(max_articles=5)

        matching_articles = []
        for source, articles in result['articles'].items():
            for article in articles:
                # 在标题和摘要中搜索关键词
                if keyword.lower() in article['title'].lower() or keyword.lower() in article['summary'].lower():
                    matching_articles.append({
                        **article,
                        'matched_source': source
                    })

                if len(matching_articles) >= max_articles:
                    break

            if len(matching_articles) >= max_articles:
                break

        return matching_articles

    def send_to_telegram(self, articles_data: Dict, chat_id: Optional[str] = None) -> bool:
        """
        发送新闻到Telegram

        Args:
            articles_data: 新闻数据（get_news_summary的返回值）
            chat_id: Telegram chat ID（None使用默认配置）

        Returns:
            是否成功发送
        """
        if not articles_data.get('articles'):
            print('[ERROR] No articles to send')
            return False

        chat_id = chat_id or CHAT_ID

        # 格式化消息
        message_parts = []
        message_parts.append(f"金融新闻速递")
        message_parts.append("=" * 50)
        message_parts.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        message_parts.append(f"来源数: {articles_data['successful_sources']}/{articles_data['total_sources']}")
        message_parts.append(f"文章数: {articles_data['total_articles']}")
        message_parts.append("")

        # 按源组织新闻
        for source, articles in articles_data['articles'].items():
            if not articles:
                continue

            for i, article in enumerate(articles[:3], 1):  # 每个源最多3篇
                message_parts.append(f"【{source}】")
                message_parts.append(f"{i}. {article['title']}")
                message_parts.append(f"   {article['summary'][:100]}...")
                message_parts.append(f"   {article['url']}")
                message_parts.append("")

        message = "\n".join(message_parts)

        # 分批发送（Telegram消息长度限制）
        max_length = 4000
        if len(message) > max_length:
            # 分批发送
            success = True
            for i in range(0, len(message), max_length):
                chunk = message[i:i+max_length]
                if not self._send_telegram_message(chunk, chat_id):
                    success = False
            return success
        else:
            return self._send_telegram_message(message, chat_id)

    def _send_telegram_message(self, message: str, chat_id: str) -> bool:
        """发送单条Telegram消息"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}

        try:
            response = requests.post(url, json=data, proxies=PROXIES, timeout=30)
            result = response.json()

            if result.get('ok'):
                return True
            else:
                print(f"[ERROR] Telegram API error: {result}")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to send: {e}")
            return False

    def set_preference(self, key: str, value):
        """设置用户偏好"""
        self.user_preferences[key] = value
        self.save_user_preferences()

    def get_preference(self, key: str, default=None):
        """获取用户偏好"""
        return self.user_preferences.get(key, default)


# ==================== OpenClaw接口函数 ====================

def fetch_news_summary(max_articles: int = 5, sources: Optional[List[str]] = None) -> str:
    """
    获取新闻摘要（OpenClaw调用接口）

    Args:
        max_articles: 每个源最多获取的文章数
        sources: 指定新闻源列表

    Returns:
        新闻摘要文本
    """
    skill = OpenClawNewsSkill()
    result = skill.get_news_summary(max_articles=max_articles, sources=sources)

    output = []
    output.append(f"抓取完成！")
    output.append(f"成功源: {result['successful_sources']}/{result['total_sources']}")
    output.append(f"总文章数: {result['total_articles']}")
    output.append("")

    for source, articles in result['articles'].items():
        if articles:
            output.append(f"[{source}]")
            for article in articles[:2]:  # 只显示前2篇
                output.append(f"  - {article['title'][:60]}...")

    return "\n".join(output)


def send_news_to_telegram(max_articles: int = 5, send: bool = True) -> str:
    """
    获取并发送新闻到Telegram（OpenClaw调用接口）

    Args:
        max_articles: 每个源最多获取的文章数
        send: 是否发送到Telegram

    Returns:
        结果描述
    """
    skill = OpenClawNewsSkill()
    result = skill.get_news_summary(max_articles=max_articles)

    output = []
    output.append(f"抓取完成！")
    output.append(f"成功源: {result['successful_sources']}/{result['total_sources']}")
    output.append(f"总文章数: {result['total_articles']}")

    if send:
        success = skill.send_to_telegram(result)
        if success:
            output.append("")
            output.append("[SUCCESS] 已发送到Telegram!")
        else:
            output.append("")
            output.append("[FAILED] 发送到Telegram失败")

    return "\n".join(output)


def search_news(keyword: str, max_articles: int = 10) -> str:
    """
    搜索关键词相关新闻（OpenClaw调用接口）

    Args:
        keyword: 搜索关键词
        max_articles: 最大文章数

    Returns:
        搜索结果文本
    """
    skill = OpenClawNewsSkill()
    articles = skill.get_news_by_keyword(keyword, max_articles)

    output = []
    output.append(f"关键词搜索: {keyword}")
    output.append(f"找到 {len(articles)} 篇相关文章")
    output.append("")

    for i, article in enumerate(articles, 1):
        output.append(f"{i}. {article['title']}")
        output.append(f"   来源: {article['matched_source']}")
        output.append(f"   链接: {article['url']}")
        output.append("")

    return "\n".join(output)


# ==================== 测试入口 ====================

if __name__ == '__main__':
    # 测试：获取1条新闻并发送到Telegram
    print("=" * 60)
    print("OpenClaw News Skill - 测试模式")
    print("=" * 60)
    print("配置: 只抓取1条新闻并发送\n")

    skill = OpenClawNewsSkill()

    # 只获取1条新闻
    result = skill.get_news_summary(max_articles=1, sources=['sina_finance'])

    print(f"状态: {result['status']}")
    print(f"文章数: {result['total_articles']}")

    if result['total_articles'] > 0:
        # 发送到Telegram
        print("\n发送到Telegram...")
        success = skill.send_to_telegram(result)

        if success:
            print("[SUCCESS] 测试完成！新闻已发送到Telegram")
        else:
            print("[FAILED] 发送失败")

        print("\n" + "=" * 60)
    else:
        print("[FAILED] 未获取到新闻")
