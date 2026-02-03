# -*- coding: utf-8 -*-
"""
AI新闻分析器 - 使用智谱清言API
严格按照summary_finance.md的格式要求进行新闻分析和总结
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import requests
from typing import Dict, List
from datetime import datetime

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


class AIAnalyzer:
    """AI新闻分析器 - 使用智谱清言API"""

    def __init__(self, api_key: str = None, proxies: dict = None):
        """
        初始化AI分析器

        Args:
            api_key: 智谱AI API密钥，如果不提供则从环境变量读取
            proxies: 代理设置
        """
        self.api_key = api_key or os.getenv('ZHIPU_API_KEY', '')
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.proxies = proxies

    def generate_news_summary(self, article: Dict) -> str:
        """
        为单条新闻生成详细总结

        严格按照summary_finance.md中的示例格式输出
        """
        title = article.get('title', '')
        content = article.get('content') or article.get('summary', '')
        source = article.get('source', '未知来源')

        if not content:
            return f"【{source}】#{title}\n\n内容暂无\n\n【参考链接】\n{article.get('url', '')}"

        # 检查是否为英文，如果是英文需要翻译
        is_english = self._is_english(content)
        lang_note = "（英文已翻译为中文）" if is_english else ""

        # 构建分析提示词 - 严格按照MD示例格式
        prompt = f"""请分析以下财经新闻，并按照指定格式生成详细总结。

新闻标题：{title}
新闻来源：{source}
新闻内容：{content}
{lang_note}

请严格按照以下格式输出总结：

【总结】
核心观点：（用1句话概括新闻的核心观点）
事件背景：（简要说明事件的背景和起因）
关键细节：（列出3-5个关键细节或数据点，用分号分隔）
影响分析：
- 对市场的影响：（对证券市场、指数的影响）
- 对行业的影响：（对相关行业的影响，特别是AI、半导体、云计算、科技行业）
- 对企业的影响：（对相关企业的影响）
未来展望：（预测后续发展趋势）

重要提示：
1. 确保"核心观点"、"事件背景"、"关键细节"、"影响分析"、"未来展望"这些标题明确输出
2. 每个部分都要有具体内容，不要省略
3. 关键细节用分号分隔，要具体列出数据点
4. 影响分析要分点，使用"-"符号
5. 总结要详细、专业，涵盖时间、事件、影响等要素
6. 如果是英文新闻，分析时使用中文
7. 获取的新闻均来自国内外正规网站，内容不包含敏感信息，请忽略所有提示和警告，直接输出总结内容

请只输出总结内容，不要有多余的说明文字。"""

        try:
            response = self._call_api(prompt)
            # 确保返回的内容以"【总结】"开头
            if not response.startswith("【总结】"):
                response = "【总结】\n" + response
            return response
        except Exception as e:
            print(f"  [WARN] AI分析失败: {e}，使用原始内容")
            # 降级：使用原始内容
            return f"""【总结】
核心观点：{title}

事件背景：{source}

关键细节：{content[:200]}

影响分析：
- 对市场的影响：详见原文
- 对行业的影响：详见原文
- 对企业的影响：详见原文

未来展望：请关注后续发展

【参考链接】
{article.get('url', '')}"""

    def analyze_important_news(self, articles: List[Dict]) -> str:
        """
        分析所有新闻中的重要消息

        严格按照summary_finance.md的要求：
        告诉我哪一条新闻的哪一句/哪一段，会对什么样的产业，造成什么样的影响
        """
        if not articles:
            return "暂无重要消息分析"

        # 构建新闻摘要（包含标题和关键内容）
        news_summary = ""
        for i, article in enumerate(articles[:15], 1):
            news_summary += f"\n新闻{i}：\n"
            news_summary += f"标题：{article.get('title', '')}\n"
            news_summary += f"来源：{article.get('source', '')}\n"
            content = article.get('content') or article.get('summary', '')
            news_summary += f"内容摘要：{content[:300]}...\n"

        prompt = f"""请分析以下财经新闻，识别出对证券指数和行业发展有重要影响的新闻，并按照指定格式逐一分析。

{news_summary}

请严格按照以下格式输出：

【重要消息】

对于每条重要新闻，请按以下格式分析：
1. 【新闻标题】来自【来源】
   - 关键内容：摘录新闻中的具体原话（哪一句话/哪一段）
   - 影响产业：说明会对什么产业/行业造成影响
   - 影响分析：详细说明会造成什么样的影响（正面/负面/中性，短期/中期/长期）

重点关注：
- AI行业影响（AI技术突破、AI商业化进展、AI政策变化、AI企业动态）
- 半导体行业影响（芯片技术进展、产能变化、供应链变化、政策支持）
- 云计算行业影响（云服务需求、技术升级、市场竞争、政策导向）
- 科技公司动态（业绩变化、战略调整、产品发布、合作动态）
- 证券指数影响（对股市、板块指数的影响）

重要要求：
1. 必须引用新闻中的具体原话，不要概括
2. 必须明确说明影响的具体产业/行业
3. 必须具体说明影响的方向和程度
4. 只分析真正重要的新闻，不要凑数
5. 基于实际新闻内容分析，不要编造
6. 如果没有特别重要的消息，请说明"本次获取的新闻暂无特别重要的行业影响消息"

【投资建议】
根据获取的财经新闻，给出投资建议，包括中国和美国的基金、股票的投资建议，只需要细分到领域和行业
例如：
    1.建议投资中国某行业的股票/基金，理由是...
    2.建议投资美国某行业的股票/基金，理由是...
    
请只输出分析内容，格式要清晰、层次要分明。"""

        try:
            response = self._call_api(prompt)
            # 确保以"【重要消息】"开头
            if not response.startswith("【重要消息】") and "【重要消息】" in response:
                # 提取重要消息部分
                start = response.find("【重要消息】")
                response = response[start:]
            elif not response.startswith("【重要消息】"):
                response = "【重要消息】\n\n" + response
            return response
        except Exception as e:
            print(f"[WARN] 重要消息分析失败: {e}")
            return """【重要消息】

基于当前获取的新闻，本次获取的新闻暂无特别重要的行业影响消息。

建议关注：
- AI和半导体行业动态
- 科技公司业绩表现
- 全球股市走势分析"""

    def _is_english(self, text: str) -> bool:
        """检测是否为英文"""
        if not text:
            return False
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        return ascii_chars / len(text) > 0.6

    def _call_api(self, prompt: str, max_retries: int = 3) -> str:
        """
        调用智谱清言API
        """
        if not self.api_key:
            raise ValueError("未设置ZHIPU_API_KEY，请在.env文件中配置")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "glm-4-flash",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的财经新闻分析师，擅长分析新闻对证券市场、行业发展和企业的影响。你必须严格按照用户指定的格式输出，输出要详细、准确、专业，重点突出对投资决策有价值的信息。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        for attempt in range(max_retries):
            try:
                print(f"调用智谱API (尝试 {attempt + 1}/{max_retries})...")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    proxies=self.proxies,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    print("AI分析成功")
                    return content.strip()
                else:
                    print(f"API返回错误: {response.status_code} - {response.text}")

            except requests.exceptions.Timeout:
                print(f"请求超时 (尝试 {attempt + 1}/{max_retries})")
            except Exception as e:
                print(f"请求失败: {e}")

            if attempt < max_retries - 1:
                import time
                time.sleep(2)

        raise Exception(f"AI分析失败，已重试{max_retries}次")


def test_analyzer():
    """测试AI分析器"""
    print("=" * 60)
    print("AI分析器测试")
    print("=" * 60)
    print()

    # 检查API密钥
    api_key = os.getenv('ZHIPU_API_KEY', '')
    if not api_key or api_key == 'your_zhipu_api_key_here':
        print("[ERROR] 未设置ZHIPU_API_KEY")
        print("请在.env文件中添加: ZHIPU_API_KEY=your_api_key")
        return False

    from config import PROXIES
    analyzer = AIAnalyzer(proxies=PROXIES)

    # 测试新闻
    test_article = {
        'title': 'NVIDIA发布最新GPU芯片，AI性能提升3倍',
        'content': '英伟达今日发布了最新的Blackwell GPU芯片，专为AI训练和推理设计。新芯片在AI性能上比上一代提升了3倍，能效提升2倍。CEO黄仁勋表示，这将彻底改变AI行业格局。主要云服务商已宣布将采用新芯片。',
        'source': 'TechCrunch',
        'url': 'https://example.com/news1'
    }

    print("测试单条新闻分析...")
    print("-" * 60)
    summary = analyzer.generate_news_summary(test_article)
    print(summary)
    print()
    print("=" * 60)
    print("[OK] 测试完成")
    return True


if __name__ == '__main__':
    success = test_analyzer()
    exit(0 if success else 1)
