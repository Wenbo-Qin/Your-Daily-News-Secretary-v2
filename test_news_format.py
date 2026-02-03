# -*- coding: utf-8 -*-
"""
测试脚本：验证新闻格式并保存
"""
import json
from datetime import datetime
from pathlib import Path
from news_fetcher_v2 import NewsFetcher
from config import PROXIES, BOT_TOKEN, CHAT_ID
import requests

def test_and_save():
    """测试并保存新闻到文件"""
    print("=" * 60)
    print("新闻格式测试")
    print("=" * 60)
    print()

    fetcher = NewsFetcher()

    # 测试新浪新闻
    print("正在获取新浪财经新闻...")
    articles = fetcher.fetch_with_retries('sina_finance', fetcher.sources['sina_finance'], max_articles=1)

    if not articles:
        print("[FAIL] 未获取到新闻")
        return False

    article = articles[0]

    # 验证必需字段
    required_fields = ['title', 'url', 'summary', 'source', 'fetched_at']
    missing_fields = [f for f in required_fields if f not in article]

    if missing_fields:
        print(f"[FAIL] 缺少字段: {missing_fields}")
        return False

    print("[OK] 新闻格式正确")
    print()
    print("-" * 60)
    print("新闻内容:")
    print("-" * 60)
    print(f"标题: {article['title']}")
    print(f"来源: {article['source']}")
    print(f"时间: {article['fetched_at'][:19]}")
    print(f"链接: {article['url']}")
    print()
    print("摘要:")
    print(article['summary'])
    print()
    print("-" * 60)
    print()

    # 保存到文件
    data_dir = Path(__file__).parent / 'data'
    data_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = data_dir / f'test_news_{timestamp}.json'

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(article, f, ensure_ascii=False, indent=2)

    print(f"[OK] 新闻已保存到: {filename}")
    print()

    # 发送到Telegram
    print("发送到Telegram...")
    message = f"""📰 测试新闻
{'=' * 40}

【来源】{article['source']}
【时间】{article['fetched_at'][:19]}

【标题】{article['title']}

【摘要】
{article['summary']}

【链接】{article['url']}

{'=' * 40}
✅ 测试成功！这是真实新闻
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}

    try:
        response = requests.post(url, json=data, proxies=PROXIES, timeout=30)
        result = response.json()

        if result.get('ok'):
            print("[OK] 新闻已发送到Telegram")
            print()
            print("=" * 60)
            print("✅ 测试完成！")
            print("=" * 60)
            print()
            print("验证结果:")
            print("  ✓ 新闻格式正确")
            print("  ✓ 内容真实有效")
            print("  ✓ 已发送到Telegram")
            print("  ✓ 数据已保存到文件")
            print()
            print("请在Telegram中查看收到的新闻消息")
            return True
        else:
            print(f"[FAIL] Telegram发送失败: {result}")
            return False

    except Exception as e:
        print(f"[FAIL] 发送错误: {e}")
        return False

if __name__ == '__main__':
    success = test_and_save()
    exit(0 if success else 1)
