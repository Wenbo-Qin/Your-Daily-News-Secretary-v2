# -*- coding: utf-8 -*-
"""
财经新闻总结测试版本 - 仅使用主要源
"""
import requests
from datetime import datetime
from news_fetcher_v2 import NewsFetcher
from ai_analyzer import AIAnalyzer
from config import PROXIES, BOT_TOKEN, CHAT_ID

def main():
    print("=" * 60)
    print("财经新闻总结测试（AI分析版）")
    print("=" * 60)
    print()

    fetcher = NewsFetcher()
    analyzer = AIAnalyzer(proxies=PROXIES)

    # 仅使用3个主要源进行测试
    sources_to_fetch = ['cnbc', 'techcrunch', 'nvidia_news']

    all_articles = []

    print("开始获取新闻...")
    print("-" * 60)

    for source in sources_to_fetch:
        print(f"正在获取 {source} 的新闻（3条）...")

        if source in fetcher.sources:
            try:
                articles = fetcher.fetch_with_retries(
                    source,
                    fetcher.sources[source],
                    max_articles=3  # 测试版每个源只获取3条
                )

                if articles:
                    all_articles.extend(articles)
                    print(f"  成功: {len(articles)} 篇")
                else:
                    print(f"  未获取到新闻")

            except Exception as e:
                print(f"  [ERROR] {e}")

        print()

    if not all_articles:
        print("[FAIL] 未获取到任何新闻")
        return False

    print("-" * 60)
    print(f"总共获取: {len(all_articles)} 篇新闻")
    print("-" * 60)
    print()

    # 获取当前时间
    now = datetime.now()
    date_str = now.strftime('%Y年%m月%d日')
    time_str = now.strftime('%H:%M')

    # 发送标题
    header = f"""【财经新闻总结测试】
📅 {date_str}  {time_str}

==================================================
"""
    print("发送标题...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": header}, proxies=PROXIES, timeout=30)

    # 按源发送新闻（每条单独发送）
    source_display_map = {
        'cnbc': 'CNBC',
        'techcrunch': 'TechCrunch',
        'nvidia_news': 'NVIDIA News'
    }

    for article in all_articles:
        source_name = article.get('source', '')
        display_name = source_display_map.get(source_name, source_name)
        print(f"[{display_name}] {article['title'][:30]}...")

        # AI分析
        print("  AI分析中...")
        try:
            ai_summary = analyzer.generate_news_summary(article)
        except Exception as e:
            print(f"  [WARN] AI分析失败: {e}")
            content = article.get('content') or article.get('summary', '')
            ai_summary = f"""【总结】
{content[:500]}

【参考链接】
{article.get('url', '')}"""

        news_item = f"""【{display_name}】{article['title']}

{ai_summary}

————————
"""

        requests.post(url, json={"chat_id": CHAT_ID, "text": news_item}, proxies=PROXIES, timeout=30)

    # 发送结尾
    footer = f"""==================================================

【重要消息】

测试版本 - 获取了 {len(all_articles)} 条新闻

==================================================
数据来源: {', '.join(source_display_map.values())}
"""

    print("发送结尾...")
    requests.post(url, json={"chat_id": CHAT_ID, "text": footer}, proxies=PROXIES, timeout=30)

    print()
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
