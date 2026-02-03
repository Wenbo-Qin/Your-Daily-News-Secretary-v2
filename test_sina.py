# -*- coding: utf-8 -*-
"""测试新浪财经网站结构"""
import requests
from bs4 import BeautifulSoup
from config import PROXIES

url = "https://finance.sina.com.cn/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print(f"访问: {url}")
response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
print(f"状态码: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'lxml')

    # 查找可能的新闻列表选择器
    selectors_to_try = [
        '#media_list_ul',
        '.news-list',
        '#newsList',
        '.list-content',
        'ul.media-list',
        'a[href*="/roll/"]',
        '.article-item'
    ]

    print("\n查找新闻列表...")
    for selector in selectors_to_try:
        items = soup.select(selector)
        if items:
            print(f"[OK] 找到 {len(items)} 条，选择器: {selector}")
            print(f"  前3条:")
            for i, item in enumerate(items[:3], 1):
                link = item.find('a', href=True) if item.name == 'li' else item
                if link:
                    print(f"    {i}. {link.get('text', '')[:50]}")
                    print(f"       链接: {link.get('href', '')[:60]}")
            break
    else:
        print("[FAIL] 未找到标准新闻列表")

    # 查找RSS链接
    print("\n查找RSS链接...")
    rss_links = soup.find_all('a', href=lambda x: x and 'rss' in str(x).lower())
    if rss_links:
        print(f"找到 {len(rss_links)} 个RSS链接:")
        for link in rss_links[:5]:
            print(f"  - {link.get('href', '')}")

    # 查找可能的新闻容器
    print("\n查找所有带href的a标签...")
    all_links = soup.find_all('a', href=True)[:20]
    print(f"前20个链接:")
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)[:50]
        if href.startswith('/') and 'finance' in href:
            print(f"  [{text}](https://finance.sina.com.cn{href})")
