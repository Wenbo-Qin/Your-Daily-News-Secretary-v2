# -*- coding: utf-8 -*-
"""测试重要消息分析"""
from ai_analyzer import AIAnalyzer
from config import PROXIES

analyzer = AIAnalyzer(proxies=PROXIES)

# 测试用例 - 使用实际的新闻
test_articles = [
    {
        'title': 'AMD发布最新营收预告未达预期',
        'content': 'AMD公司今日发布最新营收预告，低于市场预期，股价盘后下跌5%',
        'source': 'CNBC',
        'url': 'https://test.com'
    },
    {
        'title': 'AI股票交易点：2026年每月可能发生的事件',
        'content': '2026年AI行业将迎来多个重要节点，包括新产品发布和监管政策变化',
        'source': 'Yahoo Finance',
        'url': 'https://test.com'
    }
]

print('=' * 60)
print('测试 analyze_important_news 方法')
print('=' * 60)

result = analyzer.analyze_important_news(test_articles)
print('返回结果长度:', len(result))
print('返回结果内容:')
print(repr(result))
print()
print('实际输出:')
print(result)
