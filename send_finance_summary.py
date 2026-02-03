# -*- coding: utf-8 -*-
"""
财经新闻总结 - 完整AI分析版本
严格按照summary_finance.md格式输出，每10条新闻合并为一个Telegram消息
"""
import requests
import os
from datetime import datetime
from pathlib import Path
from news_fetcher_v2 import NewsFetcher
from ai_analyzer import AIAnalyzer
from config import PROXIES, BOT_TOKEN, CHAT_ID


class FinanceSummarySender:
    """财经新闻总结发送器 - 严格按照summary_finance.md格式"""

    def __init__(self):
        self.fetcher = NewsFetcher()
        self.analyzer = AIAnalyzer(proxies=PROXIES)
        self.url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        # 新闻源显示名称映射
        self.source_display_map = {
            'cnbc': 'CNBC',
            'yahoo_finance': 'Yahoo Finance',
            'techcrunch': 'TechCrunch',
            'nvidia_news': 'NVIDIA News',
            'arstechnica': 'Ars Technica',
            'theverge': 'The Verge',
            'sina_finance': '新浪财经',
            'eastmoney': '东方财富',
            'xueqiu': '雪球网',
            'tonghuashun': '同花顺',
            'china_securities': '中国证券报',
            'yicai': '第一财经',
            'marketwatch': 'MarketWatch',
            'seeking_alpha': 'Seeking Alpha',
            'ai_news': 'AI News'
        }

    def send_message(self, text: str) -> bool:
        """发送消息到Telegram"""
        data = {"chat_id": CHAT_ID, "text": text}

        try:
            response = requests.post(
                self.url,
                json=data,
                proxies=PROXIES,
                timeout=30
            )
            result = response.json()

            if result.get('ok'):
                return True
            else:
                print(f"[FAIL] 发送失败: {result}")
                return False

        except Exception as e:
            print(f"[ERROR] {e}")
            return False

    def generate_ai_summary(self, article: dict) -> str:
        """为文章生成AI详细总结"""
        print(f"  正在AI分析: {article['title'][:30]}...")

        # 检查是否配置了API密钥
        if not os.getenv('ZHIPU_API_KEY') or os.getenv('ZHIPU_API_KEY') == 'your_zhipu_api_key_here':
            print(f"  [INFO] 未配置智谱API密钥，使用原始内容")
            content = article.get('content') or article.get('summary', '')
            return f"""**总结**
核心观点：{article['title']}

事件背景：{article.get('source', '')}

关键细节：{content[:300]}

影响分析：
- 对市场的影响：详见原文
- 对行业的影响：详见原文
- 对企业的影响：详见原文

未来展望：请关注后续发展

**参考链接**
{article.get('url', '')}"""

        try:
            # 调用AI分析器
            ai_summary = self.analyzer.generate_news_summary(article)
            # 确保以**总结**开头
            if not ai_summary.startswith("总结"):
                ai_summary = "【总结】\n" + ai_summary
            # 添加参考链接
            if "参考链接" not in ai_summary:
                ai_summary += f"\n【参考链接】\n{article.get('url', '')}"
            return ai_summary
        except Exception as e:
            print(f"  [WARN] AI分析失败: {e}，使用原始内容")
            # 降级：使用原始内容
            content = article.get('content') or article.get('summary', '')
            return f"""【总结】
核心观点：{article['title']}

事件背景：{article.get('source', '')}

关键细节：{content[:300]}

影响分析：
- 对市场的影响：详见原文
- 对行业的影响：详见原文
- 对企业的影响：详见原文

未来展望：请关注后续发展

【参考链接】
{article.get('url', '')}"""

    def send_finance_summary(self):
        """发送财经新闻总结 - 严格按照summary_finance.md格式"""
        print("=" * 60)
        print("财经新闻总结")
        print("=" * 60)
        print()

        # 定义要抓取的源（国内+国外）
        sources_to_fetch = [
            # 国内中文财经网站
            'sina_finance',
            'eastmoney',
            'xueqiu',
            'tonghuashun',
            'china_securities',
            'yicai',
            # 国外财经网站
            'cnbc',
            'yahoo_finance',
            'techcrunch',
            'nvidia_news',
            'arstechnica',
            'marketwatch'
        ]

        all_articles_by_source = {}
        all_articles = []

        print("开始获取新闻...")
        print("-" * 60)

        # 获取每个源的新闻
        for source in sources_to_fetch:
            print(f"正在获取 {source} 的新闻（5条）...")

            if source in self.fetcher.sources:
                try:
                    articles = self.fetcher.fetch_with_retries(
                        source,
                        self.fetcher.sources[source],
                        max_articles=3
                    )

                    if articles:
                        all_articles_by_source[source] = articles
                        all_articles.extend(articles)
                        print(f"  成功: {len(articles)} 篇")
                    else:
                        print(f"  未获取到新闻")

                except Exception as e:
                    print(f"  [ERROR] {e}")

            print()

        if not all_articles_by_source:
            print("[FAIL] 未获取到任何新闻")
            return False

        print("-" * 60)
        print(f"总共获取: {sum(len(v) for v in all_articles_by_source.values())} 篇新闻")
        print("-" * 60)
        print()

        # 获取当前时间
        now = datetime.now()
        date_str = now.strftime('%Y年%m月%d日')
        time_str = now.strftime('%H:%M')

        # ==================== 第一部分：新闻摘要（每10条合并）====================
        print("=" * 60)
        print("第一部分：新闻摘要")
        print("=" * 60)
        print()

        # 按源组织新闻，但打乱顺序发送
        news_batch = []
        for source_name, articles in all_articles_by_source.items():
            display_name = self.source_display_map.get(source_name, source_name)

            for article in articles[:5]:
                print(f"[{display_name}] 处理中...")
                # 生成AI详细总结
                ai_summary = self.generate_ai_summary(article)

                # 严格按照summary_finance.md格式构建新闻消息
                # 格式：【来源网站】# 标题
                news_item = f"""【{display_name}】#{article['title']}

{ai_summary}"""

                news_batch.append(news_item)

        print()
        print(f"总共生成 {len(news_batch)} 条新闻")

        # 每10条新闻合并发送
        batch_size = 10
        for i in range(0, len(news_batch), batch_size):
            batch = news_batch[i:i + batch_size]
            print(f"发送第 {i // batch_size + 1} 批消息 ({len(batch)} 条新闻)...")

            # 构建合并消息
            message_parts = [
                f"【财经新闻总结】",
                f"📅 {date_str}  {time_str}",
                "",
                "=" * 60,
                ""
            ]

            # 添加新闻（每条之间用————————分隔）
            for idx, news_item in enumerate(batch, 1):
                message_parts.append(news_item)
                message_parts.append("")
                message_parts.append("————————")
                message_parts.append("")

            # 合并发送
            full_message = "\n".join(message_parts)

            # 检查消息长度，Telegram限制4096字符
            if len(full_message) > 4000:
                # 如果太长，拆分为更小的批次
                smaller_batch_size = 5
                for j in range(0, len(batch), smaller_batch_size):
                    smaller_batch = batch[j:j + smaller_batch_size]
                    smaller_parts = [
                        f"【财经新闻总结】",
                        f"📅 {date_str}  {time_str}",
                        "",
                        "=" * 60,
                        ""
                    ]
                    for news in smaller_batch:
                        smaller_parts.append(news)
                        smaller_parts.append("")
                        smaller_parts.append("————————")
                        smaller_parts.append("")
                    self.send_message("\n".join(smaller_parts))
            else:
                self.send_message(full_message)

        print()
        print("[OK] 新闻摘要发送完成")

        # ==================== 第二部分：重要消息分析 ====================
        print()
        print("=" * 60)
        print("第二部分：重要消息分析")
        print("=" * 60)
        print()

        print("正在分析重要消息...")

        # 检查是否配置了API密钥
        if not os.getenv('ZHIPU_API_KEY') or os.getenv('ZHIPU_API_KEY') == 'your_zhipu_api_key_here':
            print(f"  [INFO] 未配置智谱API密钥，跳过AI分析")
            important_analysis = """**重要消息**

基于当前获取的新闻，本次获取的新闻暂无特别重要的行业影响消息。

建议关注：
- AI和半导体行业动态
- 科技公司业绩表现
- 全球股市走势分析"""
        else:
            try:
                important_analysis = self.analyzer.analyze_important_news(all_articles)
                # 确保以**重要消息**开头
                if not important_analysis.startswith("【重要消息】"):
                    important_analysis = "【重要消息】\n\n" + important_analysis
            except Exception as e:
                print(f"[WARN] AI分析失败: {e}")
                important_analysis = """【重要消息】

基于当前获取的新闻，本次获取的新闻暂无特别重要的行业影响消息。

建议关注：
- AI和半导体行业动态
- 科技公司业绩表现
- 全球股市走势分析"""

        # 发送重要消息分析
        footer = f"""==================================================

{important_analysis}

==================================================
数据来源: {', '.join(set(self.source_display_map.get(s, s) for s in all_articles_by_source.keys()))}
"""

        print("发送重要消息分析...")
        self.send_message(footer)

        print()
        print("=" * 60)
        print("财经新闻总结完成！")
        print("=" * 60)
        print()

        return True


def main():
    """主函数"""
    sender = FinanceSummarySender()
    success = sender.send_finance_summary()
    return success


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
