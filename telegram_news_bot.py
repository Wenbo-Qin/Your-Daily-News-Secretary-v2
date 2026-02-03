# -*- coding: utf-8 -*-
"""
Telegram新闻Bot
在Telegram聊天框中直接使用命令获取金融新闻
"""
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict

# 导入配置
from config import PROXIES, BOT_TOKEN, CHAT_ID
from openclaw_news_skill import OpenClawNewsSkill

class TelegramNewsBot:
    """Telegram新闻Bot"""

    def __init__(self):
        self.skill = OpenClawNewsSkill()
        self.last_update_file = Path(__file__).parent / 'data' / 'last_update_id.txt'

    def send_message(self, chat_id: str, text: str) -> bool:
        """发送消息到Telegram"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        # 处理长消息
        max_length = 4000
        if len(text) > max_length:
            # 分批发送
            for i in range(0, len(text), max_length):
                chunk = text[i:i+max_length]
                data = {"chat_id": chat_id, "text": chunk}
                try:
                    requests.post(url, json=data, proxies=PROXIES, timeout=30)
                except:
                    pass
            return True

        data = {"chat_id": chat_id, "text": text}

        try:
            response = requests.post(url, json=data, proxies=PROXIES, timeout=30)
            result = response.json()
            return result.get('ok', False)
        except Exception as e:
            print(f"发送失败: {e}")
            return False

    def get_news_message(self, max_articles: int = 5) -> str:
        """获取新闻摘要消息"""
        result = self.skill.get_news_summary(max_articles=max_articles)

        lines = []
        lines.append("📰 金融新闻速递")
        lines.append("=" * 40)
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"📊 成功源: {result['successful_sources']}/{result['total_sources']}")
        lines.append(f"📝 总文章数: {result['total_articles']}")
        lines.append("")

        # 按源显示新闻
        count = 0
        for source, articles in result['articles'].items():
            if not articles:
                continue

            for article in articles[:2]:  # 每个源最多2篇
                count += 1
                if count > 10:  # 最多显示10篇
                    break

                lines.append(f"【{source}】")
                lines.append(f"🔹 {article['title'][:60]}")
                lines.append(f"   {article['summary'][:80]}...")
                lines.append("")

            if count > 10:
                break

        lines.append("=" * 40)
        return "\n".join(lines)

    def handle_command(self, chat_id: str, text: str) -> str:
        """处理命令"""
        text = text.strip()

        # 帮助命令
        if text in ['/help', '/start', 'help', '帮助']:
            return """📰 金融新闻Bot 使用指南

可用命令：
/news 或 新闻 - 获取最新新闻摘要
/news5 - 获取5篇新闻
/news10 - 获取10篇
/search 关键词 - 搜索新闻
/sina - 只获取新浪新闻
/status - 查看系统状态

例如：
• /news
• /news5
• /search AI
• /sina
"""

        # 获取新闻
        elif text in ['/news', '新闻', '/n']:
            return self.get_news_message(max_articles=5)

        elif text in ['/news5']:
            return self.get_news_message(max_articles=5)

        elif text in ['/news10']:
            return self.get_news_message(max_articles=10)

        elif text in ['/sina', '新浪']:
            result = self.skill.get_news_summary(max_articles=5, sources=['sina_finance'])
            return self._format_source_news(result, '新浪财经')

        elif text.startswith('/search ') or text.startswith('搜索 '):
            keyword = text.split(' ', 1)[1] if ' ' in text else ''
            if keyword:
                articles = self.skill.get_news_by_keyword(keyword, max_articles=10)
                return self._format_search_results(keyword, articles)
            else:
                return "请提供搜索关键词，例如：/search AI"

        elif text in ['/status', '状态']:
            sources = self.skill.fetcher.sources
            enabled = [s for s in sources.values() if s.get('enabled', False)]

            return f"""📊 系统状态

配置的源: {len(sources)}
启用的源: {len(enabled)}

最近成功的方法:
{self._get_success_methods_status()}
"""

        else:
            return "未知命令。发送 /help 查看帮助。"

    def _format_source_news(self, result: Dict, source_name: str) -> str:
        """格式化单个源的新闻"""
        lines = []
        lines.append(f"📰 {source_name}")
        lines.append("=" * 40)

        articles = result['articles'].get(source_name, [])
        if not articles:
            lines.append("暂无新闻")
        else:
            for i, article in enumerate(articles[:5], 1):
                lines.append(f"{i}. {article['title']}")
                lines.append(f"   {article['summary'][:80]}...")
                lines.append("")

        lines.append("=" * 40)
        return "\n".join(lines)

    def _format_search_results(self, keyword: str, articles: list) -> str:
        """格式化搜索结果"""
        lines = []
        lines.append(f"🔍 搜索: {keyword}")
        lines.append("=" * 40)

        if not articles:
            lines.append("未找到相关新闻")
        else:
            for i, article in enumerate(articles[:10], 1):
                lines.append(f"{i}. {article['title']}")
                lines.append(f"   来源: {article['matched_source']}")
                lines.append(f"   {article['summary'][:60]}...")
                lines.append("")

        lines.append("=" * 40)
        return "\n".join(lines)

    def _get_success_methods_status(self) -> str:
        """获取成功方法状态"""
        try:
            methods_file = Path(__file__).parent / 'data' / 'success_methods.json'
            if methods_file.exists():
                with open(methods_file, 'r', encoding='utf-8') as f:
                    methods = json.load(f)

                lines = []
                for source, method in list(methods.items())[:10]:
                    lines.append(f"  {source}: {method}")

                if len(methods) > 10:
                    lines.append(f"  ... 还有 {len(methods) - 10} 个")

                return "\n".join(lines)
        except:
            pass

        return "  暂无记录"


def run_webhook_mode():
    """Webhook模式（需要部署到服务器）"""
    print("Webhook模式需要服务器部署，暂不支持")
    print("请使用 polling 模式或直接命令测试")


def run_test_message():
    """运行测试：发送一条新闻"""
    print("=" * 60)
    print("Telegram Bot 测试模式")
    print("=" * 60)
    print("配置: 发送1条新闻到Telegram\n")

    bot = TelegramNewsBot()

    # 获取1条新闻
    print("正在获取新闻...")
    result = bot.skill.get_news_summary(max_articles=1, sources=['sina_finance'])

    if result['total_articles'] > 0:
        # 格式化消息
        message = bot._format_source_news(result, '新浪财经')

        # 发送到Telegram
        print("发送到Telegram...")
        success = bot.send_message(CHAT_ID, message)

        if success:
            print("\n[SUCCESS] 测试成功！新闻已发送到Telegram")
            print("请在Telegram中查看消息")
        else:
            print("\n[FAILED] 发送失败")

        print("=" * 60)
        return success
    else:
        print("\n[FAILED] 未获取到新闻")
        return False


if __name__ == '__main__':
    # 测试模式：发送一条新闻
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        success = run_test_message()
        sys.exit(0 if success else 1)

    # 交互模式：处理命令
    elif len(sys.argv) > 1 and sys.argv[1] == '--cmd':
        if len(sys.argv) < 3:
            print("用法: python telegram_news_bot.py --cmd '命令'")
            print("例如: python telegram_news_bot.py --cmd '/news'")
            sys.exit(1)

        bot = TelegramNewsBot()
        command = sys.argv[2]
        message = bot.handle_command(CHAT_ID, command)

        print("发送消息到Telegram...")
        success = bot.send_message(CHAT_ID, message)

        if success:
            print("[SUCCESS] 消息已发送")
        else:
            print("[FAILED] 发送失败")

        sys.exit(0 if success else 1)

    else:
        print("""
Telegram新闻Bot使用说明：

1. 测试模式（发送1条新闻）:
   python telegram_news_bot.py --test

2. 命令模式（执行指定命令）:
   python telegram_news_bot.py --cmd '/news'
   python telegram_news_bot.py --cmd '/help'
   python telegram_news_bot.py --cmd '/sina'
   python telegram_news_bot.py --cmd '/search AI'

3. 在Telegram中使用:
   直接向Bot发送以下命令：
   • /news - 获取新闻摘要
   • /news5 - 获取5篇新闻
   • /sina - 获取新浪新闻
   • /search 关键词 - 搜索新闻
   • /help - 查看帮助
        """)
