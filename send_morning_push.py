# -*- coding: utf-8 -*-
"""
早间新闻推送 - 完整格式（10条新闻合并发送）
"""
import json
import requests
from datetime import datetime
from pathlib import Path
from news_fetcher_v2 import NewsFetcher
from config import PROXIES, BOT_TOKEN, CHAT_ID

def send_morning_push():
    """发送早间新闻推送 - 10条新闻合并发送"""
    print("=" * 60)
    print("早间新闻推送")
    print("=" * 60)
    print()

    fetcher = NewsFetcher()

    # 获取多个源的新闻
    all_articles = []
    sources_to_try = ['cnbc', 'yahoo_finance', 'techcrunch', 'nvidia_news', 'arstechnica']

    for source in sources_to_try:
        if source in fetcher.sources:
            print(f"正在获取 {source} 的新闻...")
            articles = fetcher.fetch_with_retries(
                source,
                fetcher.sources[source],
                max_articles=3
            )
            if articles:
                all_articles.extend(articles)
                print(f"  成功: {len(articles)} 篇")
            print()

    if not all_articles:
        print("[FAIL] 未获取到任何新闻")
        return False

    # 按优先级排序，取前10条
    priority_articles = sorted(all_articles, key=lambda x: x.get('priority_score', 0), reverse=True)[:10]

    print(f"总共获取 {len(all_articles)} 篇新闻")
    print(f"选取前 {len(priority_articles)} 篇发送")
    print()

    now = datetime.now()
    date_str = now.strftime('%Y年%m月%d日')
    time_str = now.strftime('%H:%M')

    # 构建完整消息
    message_parts = []
    message_parts.append(f"【金融新闻摘要】")
    message_parts.append(f"📅 {date_str}  {time_str}")
    message_parts.append("")
    message_parts.append("=" * 60)
    message_parts.append("")

    # 添加10条新闻
    for i, article in enumerate(priority_articles, 1):
        message_parts.append(f"【{i}】{article['title']}")
        message_parts.append("")

        # 来源和时间
        source_display = article.get('source', '未知')
        fetched_time = article.get('fetched_at', '')[:19].replace('T', ' ')
        message_parts.append(f"来源: {source_display}")
        message_parts.append(f"时间: {fetched_time}")
        message_parts.append("")

        # 链接
        url_link = article.get('url', '')
        message_parts.append(f"链接: {url_link}")
        message_parts.append("")
        message_parts.append("-" * 60)
        message_parts.append("")

    # 结尾
    message_parts.append("=" * 60)
    message_parts.append(f"本次推送共 {len(priority_articles)} 条新闻")
    message_parts.append("数据来源: CNBC, Yahoo Finance, TechCrunch, NVIDIA, Ars Technica")
    message_parts.append("=" * 60)

    full_message = "\n".join(message_parts)

    print(f"消息长度: {len(full_message)} 字符")
    print()

    # 发送完整消息
    print("发送到Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": full_message}

    try:
        response = requests.post(url, json=data, proxies=PROXIES, timeout=30)
        result = response.json()

        if result.get('ok'):
            print("[OK] 推送成功！")
            print()
            print("=" * 60)
            print("早间新闻推送完成！")
            print("=" * 60)
            print()
            print(f"[OK] 成功发送了 {len(priority_articles)} 条新闻")
            print("10条新闻已合并到一个Telegram消息中")
            return True
        else:
            print(f"[FAIL] 推送失败: {result}")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == '__main__':
    success = send_morning_push()
    exit(0 if success else 1)
