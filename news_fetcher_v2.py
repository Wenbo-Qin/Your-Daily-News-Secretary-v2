# -*- coding: utf-8 -*-
"""
通用新闻抓取器 V2
- 支持所有配置的新闻源
- 智能重试机制（5次，不同方法）
- 成功方法自动封装
- 灵活错误处理
"""
import sys
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import re
import time
import yaml
from typing import List, Dict, Optional, Callable

# 导入配置
from config import PROXIES, BOT_TOKEN, CHAT_ID

class NewsFetcher:
    """通用新闻抓取器"""

    def __init__(self):
        self.config_file = Path(__file__).parent / 'config' / 'sources.yaml'
        self.sources = self.load_sources()
        self.success_methods = {}  # 记录每个源的成功方法
        self.load_success_methods()

    def load_sources(self) -> Dict:
        """加载新闻源配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('sources', {})
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}

    def load_success_methods(self):
        """加载已保存的成功方法"""
        methods_file = Path(__file__).parent / 'data' / 'success_methods.json'
        if methods_file.exists():
            try:
                with open(methods_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 将保存的方法名转换为实际方法引用
                    for source_name, method_name in data.items():
                        if method_name == '_method_rss_beautifulsoup':
                            self.success_methods[source_name] = self._method_rss_beautifulsoup
                        elif method_name == '_method_rss_requests':
                            self.success_methods[source_name] = self._method_rss_requests
                        elif method_name == '_method_scrape_beautifulsoup':
                            self.success_methods[source_name] = self._method_scrape_beautifulsoup
                        elif method_name == '_method_scrape_requests':
                            self.success_methods[source_name] = self._method_scrape_requests
                        elif method_name == '_method_generic':
                            self.success_methods[source_name] = self._method_generic
                print(f"加载了 {len(self.success_methods)} 个源的成功方法")
            except Exception as e:
                print(f"加载成功方法失败: {e}")

    def save_success_methods(self):
        """保存成功方法到本地"""
        data_dir = Path(__file__).parent / 'data'
        data_dir.mkdir(exist_ok=True)

        # 保存方法名而不是方法对象（因为方法对象不可序列化）
        methods_to_save = {}
        for source_name, method in self.success_methods.items():
            methods_to_save[source_name] = method.__name__

        methods_file = data_dir / 'success_methods.json'
        with open(methods_file, 'w', encoding='utf-8') as f:
            json.dump(methods_to_save, f, ensure_ascii=False, indent=2)

        print(f"成功方法已保存到: {methods_file}")

    def is_english(self, text: str) -> bool:
        """检测是否为英文"""
        if not text:
            return False
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        return ascii_chars / len(text) > 0.6

    def translate_to_chinese(self, text: str) -> str:
        """翻译为中文"""
        if not text or not self.is_english(text):
            return text

        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'en',
                'tl': 'zh-CN',
                'dt': 't',
                'q': text
            }

            response = requests.get(url, params=params, proxies=PROXIES, timeout=30)
            result = response.json()

            if result and result[0]:
                translated = ''.join([item[0] for item in result[0] if item[0]])
                return translated

        except Exception as e:
            pass

        return text

    def fetch_full_article(self, url: str) -> str:
        """获取文章完整内容，支持中文财经网站"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        try:
            response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')

            # 中文财经网站专用选择器
            content_selectors = [
                '#artibody',  # 新浪财经
                '.article-content',  # 通用
                '#article-body',  # 东方财富
                '.article-body',
                'article',
                '.post-content',
                '.entry-content',
                '#content',
                '.article',
                '#article',
                '.news-content',
                '.story-body',
                '[itemprop="articleBody"]',
                '.RichTextBody',
                '.body-content',
                '.blkContainerSblkCon',  # 新浪财经特定
                '.Body',  # 东方财富特定
                '#ContentBody',
                '.em_con',
                '.article__bd__content',  # 雪球网特定
                '.detail-content',
                '#articleContent',  # 证券时报特定
                '.content-text',  # 第一财经特定
                '.f_article',
                'main',
                '.post-body',
                '.content',
                'div.article',
                'div.post-content',
                'p',
                'div p',
                'span[data-testid="article-body"]',
                'article p',
                '.text-content',
                'div[class*="content"]'
            ]

            for selector in content_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        paragraphs = elem.find_all('p')
                        content = ' '.join([p.get_text(strip=True)
                                        for p in paragraphs[:20]])
                        if len(content) > 100:
                            return content
                except:
                    continue

            # 如果所有选择器都失败，尝试直接获取所有段落
            all_paragraphs = soup.find_all('p')
            if all_paragraphs:
                content = ' '.join([p.get_text(strip=True)
                                for p in all_paragraphs[:25]])
                if len(content) > 100:
                    return content

            return ""

        except Exception as e:
            return ""

    def fetch_with_retries(self, source_name: str, source_config: Dict, max_articles: int = 5) -> List[Dict]:
        """带重试机制的抓取"""
        articles = []

        # 检查是否有保存的成功方法
        if source_name in self.success_methods:
            print(f"  使用已知成功方法...")
            try:
                method = self.success_methods[source_name]
                articles = method(source_name, max_articles, source_config)
                if articles:
                    print(f"  成功: {len(articles)} 篇")
                    return articles
            except Exception as e:
                print(f"  已知方法失败: {e}，尝试其他方法...")

        # 获取源类型
        source_type = source_config.get('type', 'rss')
        enabled = source_config.get('enabled', False)

        if not enabled:
            print(f"  源已禁用")
            return []

        # 定义多种抓取方法（优先级从高到低）
        methods = []

        # 首先添加专用方法
        if source_name == 'sina_finance':
            methods.append(self._method_sina_finance_special)
        elif source_name == 'eastmoney':
            methods.append(self._method_eastmoney_special)
        elif source_name == 'tonghuashun':
            methods.append(self._method_tonghuashun_special)
        elif source_name == 'china_securities':
            methods.append(self._method_china_securities_special)
        elif source_name in ['securities_times', 'tencent_finance', 'sohu_finance']:
            methods.append(self._method_chinese_news_sites)

        if source_type == 'rss':
            rss_feeds = source_config.get('rss_feeds', [])
            # 方法1: BeautifulSoup XML解析
            methods.append(self._method_rss_beautifulsoup)
            # 方法2: 直接HTTP请求
            methods.append(self._method_rss_requests)
            # 方法3-4: 为每个RSS feed尝试不同User-Agent（最多2个）
            for feed_url in rss_feeds[:2]:
                methods.append(lambda s, n, f, url=feed_url: self._method_rss_with_ua(s, n, f, url))
            # 最后添加通用方法
            methods.append(self._method_generic)

        elif source_type == 'scrape':
            methods.extend([
                self._method_scrape_beautifulsoup,
                self._method_scrape_requests,
                self._method_generic
            ])

        # 尝试每种方法，最多7次（增加了专用方法）
        max_attempts = min(len(methods), 7)
        for attempt, method in enumerate(methods[:max_attempts], 1):
            print(f"  尝试方法 {attempt}/{max_attempts}...")

            try:
                articles = method(source_name, max_articles, source_config)
                if articles and len(articles) > 0:
                    print(f"  [成功] 方法 {attempt} 获取到 {len(articles)} 篇")

                    # 保存成功方法
                    self.success_methods[source_name] = method

                    return articles

            except Exception as e:
                print(f"  方法 {attempt} 失败: {str(e)[:100]}")
                time.sleep(1)  # 等待1秒后重试

                if attempt == max_attempts:
                    print(f"  [放弃] {source_name} 所有方法都失败")

        return articles

    # ==================== RSS方法 ====================

    def _method_rss_beautifulsoup(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """方法1: 使用BeautifulSoup解析RSS - 尝试所有RSS源"""
        rss_feeds = source_config.get('rss_feeds', [])

        # 尝试所有RSS feeds，直到获取到足够的新闻
        articles = []
        articles_per_feed = max(1, max_articles // len(rss_feeds)) if len(rss_feeds) > 0 else max_articles

        for feed_url in rss_feeds:
            if len(articles) >= max_articles:
                break

            try:
                print(f"    BeautifulSoup解析: {feed_url[:50]}...")
                headers = {'User-Agent': 'Mozilla/5.0'}

                # 增加超时时间，使用HTTP避免SSL问题
                if feed_url.startswith('https://'):
                    feed_url_http = feed_url.replace('https://', 'http://')
                    urls_to_try = [feed_url, feed_url_http]
                else:
                    urls_to_try = [feed_url]

                for url in urls_to_try:
                    if len(articles) >= max_articles:
                        break

                    try:
                        response = requests.get(url, headers=headers, proxies=PROXIES, timeout=20)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.content, 'xml')
                        items = soup.find_all('item')[:articles_per_feed + 2]

                        for item in items:
                            if len(articles) >= max_articles:
                                break

                            title = item.find('title')
                            link = item.find('link')
                            description = item.find('description')

                            if title and link:
                                title_text = title.get_text(strip=True)
                                link_text = link.get_text(strip=True)
                                desc_text = description.get_text(strip=True) if description else ""

                                if title_text and link_text:
                                    # 清理HTML标签
                                    import re
                                    desc_text = re.sub('<[^<]+?>', '', desc_text)
                                    desc_text = desc_text.strip()

                                    # 策略1: 优先使用description（更稳定）
                                    content = desc_text if desc_text else ""

                                    # 策略2: 如果description为空，尝试获取全文
                                    if not content or len(content) < 20:
                                        full_content = self.fetch_full_article(link_text)
                                        if full_content:
                                            content = full_content[:500]

                                    # 策略3: 如果仍然没有内容，使用标题
                                    if not content:
                                        content = title_text

                                    # 翻译
                                    if self.is_english(title_text):
                                        title_text = self.translate_to_chinese(title_text)
                                        content = self.translate_to_chinese(content)

                                    summary = self._generate_summary(title_text, content)

                                    articles.append({
                                        'title': title_text,
                                        'url': link_text,
                                        'content': content[:2000],
                                        'summary': summary,
                                        'source': source_name,
                                        'fetched_at': datetime.now().isoformat()
                                    })

                        if articles:
                            print(f"      从 {url[:30]}... 获取到 {len(articles)} 篇")
                            break

                    except Exception as e:
                        continue

            except Exception as e:
                print(f"    RSS解析失败: {str(e)[:60]}")
                continue

        return articles

    def _method_rss_requests(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """方法2: 直接HTTP请求RSS（无解析）"""
        rss_feeds = source_config.get('rss_feeds', [])

        for feed_url in rss_feeds[:1]:
            articles = []
            try:
                print(f"    直接HTTP请求: {feed_url[:50]}...")
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'application/rss+xml, application/xml, */*'
                }

                response = requests.get(feed_url, headers=headers, proxies=PROXIES, timeout=30)
                response.raise_for_status()

                # 尝试解析XML
                soup = BeautifulSoup(response.content, 'xml')

                items = soup.find_all('item')[:max_articles]

                for item in items:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')

                    if title and link:
                        title_text = title.get_text(strip=True)
                        link_text = link.get_text(strip=True)
                        desc_text = description.get_text(strip=True) if description else ""

                        if title_text and link_text:
                            content = self.fetch_full_article(link_text)
                            if not content or len(content) < 50:
                                content = desc_text
                            if not content or len(content) < 20:
                                continue

                            if self.is_english(title_text):
                                title_text = self.translate_to_chinese(title_text)
                                content = self.translate_to_chinese(content)

                            summary = self._generate_summary(title_text, content)

                            articles.append({
                                'title': title_text,
                                'url': link_text,
                                'content': content[:2000],
                                'summary': summary,
                                'source': source_name,
                                'fetched_at': datetime.now().isoformat()
                            })

                if articles:
                    return articles

            except Exception as e:
                print(f"    直接请求失败: {str(e)[:80]}")
                continue

        return []

    def _method_rss_with_ua(self, source_name: str, max_articles: int, source_config: Dict, feed_url: str) -> List[Dict]:
        """方法3-5: RSS使用不同User-Agent"""
        articles = []
        try:
            print(f"    尝试不同User-Agent...")

            # 不同User-Agent列表
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Googlebot/2.1 (+http://www.google.com/bot.html)',
                'Mozilla/5.0 (compatible; RSS/1.1; +http://www.google.com/rss)'
            ]

            for ua in user_agents:
                try:
                    headers = {'User-Agent': ua}
                    response = requests.get(feed_url, headers=headers, proxies=PROXIES, timeout=30)

                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')[:max_articles]

                    for item in items:
                        title = item.find('title')
                        link = item.find('link')
                        description = item.find('description')

                        if title and link:
                            title_text = title.get_text(strip=True)
                            link_text = link.get_text(strip=True)
                            desc_text = description.get_text(strip=True) if description else ""

                            content = self.fetch_full_article(link_text)
                            if not content or len(content) < 50:
                                content = desc_text
                            if not content or len(content) < 20:
                                continue

                            if self.is_english(title_text):
                                title_text = self.translate_to_chinese(title_text)
                                content = self.translate_to_chinese(content)

                            summary = self._generate_summary(title_text, content)

                            articles.append({
                                'title': title_text,
                                'url': link_text,
                                'content': content[:2000],
                                'summary': summary,
                                'source': source_name,
                                'fetched_at': datetime.now().isoformat()
                            })

                    if articles:
                        print(f"    UA {ua[:30]}... 成功")
                        return articles

                except Exception as e:
                    continue

        except Exception as e:
            print(f"    UA方法失败: {str(e)[:80]}")

        return articles

    # ==================== 抓取方法 ====================

    def _method_scrape_beautifulsoup(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """方法1: BeautifulSoup网页抓取"""
        scrape_config = source_config.get('scrape_config', {})
        article_list_url = scrape_config.get('article_list')
        article_selector = scrape_config.get('article_selector')

        if not article_list_url:
            return []

        articles = []
        try:
            print(f"    BS抓取: {article_list_url}")

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(article_list_url, headers=headers, proxies=PROXIES, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # 查找文章链接
            news_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                title = a.get_text(strip=True)

                if len(title) > 10:
                    if not href.startswith('http'):
                        base_url = scrape_config.get('base_url', '')
                        if base_url:
                            href = base_url.rstrip('/') + '/' + href.lstrip('/')

                    news_links.append({'title': title, 'url': href})

                    if len(news_links) >= max_articles:
                        break

            # 抓取文章内容
            for item in news_links[:max_articles]:
                content = self.fetch_full_article(item['url'])
                if content and len(content) > 100:
                    if self.is_english(item['title']):
                        item['title'] = self.translate_to_chinese(item['title'])
                        content = self.translate_to_chinese(content)

                    summary = self._generate_summary(item['title'], content)

                    articles.append({
                        'title': item['title'],
                        'url': item['url'],
                        'content': content[:2000],
                        'summary': summary,
                        'source': source_name,
                        'fetched_at': datetime.now().isoformat()
                    })

            if articles:
                return articles

        except Exception as e:
            print(f"    BS抓取失败: {str(e)[:80]}")

        return []

    def _method_scrape_requests(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """方法2: 使用requests直接抓取"""
        scrape_config = source_config.get('scrape_config', {})
        article_list_url = scrape_config.get('article_list')

        if not article_list_url:
            return []

        articles = []
        try:
            print(f"    Requests抓取: {article_list_url}")
            headers = {'User-Agent': 'Mozilla/5.0'}

            response = requests.get(article_list_url, headers=headers, proxies=PROXIES, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            news_links = soup.select('a[href]')

            for a in news_links[:max_articles]:
                href = a.get('href', '')
                title = a.get_text(strip=True)

                if title and href and len(title) > 10:
                    content = self.fetch_full_article(href)
                    if content and len(content) > 100:
                        if self.is_english(title):
                            title = self.translate_to_chinese(title)
                            content = self.translate_to_chinese(content)

                        summary = self._generate_summary(title, content)

                        articles.append({
                            'title': title,
                            'url': href,
                            'content': content[:2000],
                            'summary': summary,
                            'source': source_name,
                            'fetched_at': datetime.now().isoformat()
                        })

            if articles:
                return articles

        except Exception as e:
            print(f"    Requests抓取失败: {str(e)[:80]}")

        return []

    def _method_sina_finance_special(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """新浪财经专用方法：直接从主网站抓取（不使用RSS）"""
        if source_name != 'sina_finance':
            return []

        print(f"    新浪财经专用方法（直接抓取主网站）...")
        articles = []

        try:
            # 直接从新浪财经主网站抓取
            url = "https://finance.sina.com.cn/"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            print(f"    访问: {url}")
            response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
            print(f"    状态码: {response.status_code}")

            if response.status_code != 200:
                return articles

            soup = BeautifulSoup(response.content, 'lxml')

            # 查找所有包含 /roll/ 的链接（新浪财经新闻的典型模式）
            news_links = soup.find_all('a', href=lambda x: x and '/roll/' in str(x))

            print(f"    找到 {len(news_links)} 个 /roll/ 链接")

            # 处理每个新闻链接
            seen_urls = set()
            for link_tag in news_links:
                if len(articles) >= max_articles:
                    break

                href = link_tag.get('href', '')
                title = link_tag.get_text(strip=True)

                # 跳过空标题或已见过的URL
                if not title or not href or href in seen_urls:
                    continue

                # 确保URL是完整的
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://finance.sina.com.cn' + href

                seen_urls.add(href)

                # 跳过非新闻链接
                if 'index.d.html' in href or 'page=' in href:
                    continue

                print(f"    处理: {title[:30]}...")

                # 尝试获取全文内容
                content = self.fetch_full_article(href)

                # 如果获取失败，使用标题作为内容
                if not content or len(content) < 20:
                    content = title

                summary = self._generate_summary(title, content)

                articles.append({
                    'title': title,
                    'url': href,
                    'content': content[:2000],
                    'summary': summary,
                    'source': source_name,
                    'fetched_at': datetime.now().isoformat()
                })

            print(f"    新浪财经成功获取 {len(articles)} 篇")

        except Exception as e:
            print(f"    新浪财经专用方法失败: {str(e)[:80]}")

        return articles

    def _method_eastmoney_special(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """东方财富专用方法"""
        if source_name != 'eastmoney':
            return []

        print(f"    东方财富专用方法...")
        articles = []

        try:
            # 东方财富的首页和财经要闻页面
            urls_to_try = [
                "https://www.eastmoney.com/default.html",
                "https://www.eastmoney.com/"
            ]

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }

            for url in urls_to_try:
                try:
                    print(f"      尝试: {url[:50]}...")
                    response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'lxml')

                    # 东方财富首页的新闻列表选择器（多种可能）
                    selectors = [
                        '#media_list_ul li',
                        '.list-content li',
                        '.news-item',
                        'ul.media-list li',
                        '#newsContent li',
                        'a[href*="/news/"]'
                    ]

                    news_items = []
                    for selector in selectors:
                        items = soup.select(selector)
                        if items:
                            news_items = items[:max_articles * 2]
                            print(f"      找到 {len(items)} 条，使用选择器: {selector}")
                            break

                    if not news_items:
                        print(f"      未找到新闻列表")
                        continue

                    for item in news_items:
                        # 查找链接和标题
                        if item.name == 'li':
                            link_tag = item.find('a', href=True)
                            if link_tag:
                                title = link_tag.get_text(strip=True)
                                href = link_tag.get('href', '')
                            else:
                                continue
                        else:
                            title = item.get_text(strip=True)
                            href = item.get('href', '')

                        if title and href and len(title) > 10:
                            # 处理相对URL
                            if not href.startswith('http'):
                                if href.startswith('//'):
                                    href = 'https:' + href
                                elif href.startswith('/'):
                                    href = 'https://www.eastmoney.com' + href
                                else:
                                    href = 'https://www.eastmoney.com/' + href

                            # 获取时间标签作为备选内容
                            time_tag = item.find(['span', 'time'], class_=lambda x: x and 'time' in str(x).lower())
                            time_str = time_tag.get_text(strip=True) if time_tag else ""

                            # 获取内容
                            content = self.fetch_full_article(href)
                            if not content or len(content) < 50:
                                content = f"{title} {time_str}".strip()

                            if not content or len(content) < 20:
                                content = title

                            summary = self._generate_summary(title, content)

                            articles.append({
                                'title': title,
                                'url': href,
                                'content': content[:2000],
                                'summary': summary,
                                'source': source_name,
                                'fetched_at': datetime.now().isoformat()
                            })

                            # 达到目标数量后停止
                            if len(articles) >= max_articles:
                                break

                    if articles:
                        print(f"    东方财富成功获取 {len(articles)} 篇")
                        return articles

                except Exception as e:
                    print(f"      东方财富尝试 {url[:40]} 失败: {str(e)[:50]}")
                    continue

        except Exception as e:
            print(f"    东方财富专用方法失败: {str(e)[:80]}")

        return articles

    def _method_chinese_news_sites(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """中文财经网站通用方法（中国证券报等）"""
        if source_name not in ['china_securities', 'tencent_finance', 'sohu_finance']:
            return []

        print(f"    中文网站通用方法...")
        articles = []

        try:
            url = source_config.get('url', '')
            if not url:
                return []

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }

            response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')

            # 中文网站常见选择器
            selectors = [
                '.news-list li',
                '.news-item',
                '.article-list li',
                'ul.news li',
                '.content-list li',
                'a[href*="/article/"]',
                'a[href*="/news/"]'
            ]

            for selector in selectors:
                items = soup.select(selector)[:max_articles * 2]  # 获取更多以便筛选

                if not items:
                    continue

                for item in items:
                    # 如果是li标签，查找其中的a标签
                    if item.name == 'li':
                        link_tag = item.find('a', href=True)
                        if link_tag:
                            title = link_tag.get_text(strip=True)
                            href = link_tag.get('href', '')
                        else:
                            continue
                    else:
                        title = item.get_text(strip=True)
                        href = item.get('href', '')

                    if title and href and len(title) > 10:
                        # 处理相对URL
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                href = url.rstrip('/') + href
                            else:
                                href = url.rstrip('/') + '/' + href

                        # 获取内容
                        content = self.fetch_full_article(href)

                        # 如果全文获取失败，使用标题+来源
                        if not content or len(content) < 50:
                            # 尝试从item中提取摘要
                            summary_tag = item.find(['p', 'span', 'div'], class_=lambda x: x and ('summary' in str(x).lower() or 'desc' in str(x).lower() or 'excerpt' in str(x).lower()))
                            if summary_tag:
                                content = summary_tag.get_text(strip=True)
                            else:
                                content = f"{title}"

                        if not content or len(content) < 20:
                            continue

                        summary = self._generate_summary(title, content)

                        articles.append({
                            'title': title,
                            'url': href,
                            'content': content[:2000],
                            'summary': summary,
                            'source': source_name,
                            'fetched_at': datetime.now().isoformat()
                        })

                    if len(articles) >= max_articles:
                        break

                if articles:
                    break

            if articles:
                print(f"    中文网站方法成功获取 {len(articles)} 篇")
                return articles

        except Exception as e:
            print(f"    中文网站方法失败: {str(e)[:80]}")

        return []

    def _method_tonghuashun_special(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """同花顺专用方法"""
        if source_name != 'tonghuashun':
            return []

        print(f"    同花顺专用方法...")
        articles = []

        try:
            urls_to_try = [
                "https://www.10jqka.com.cn/"
            ]

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.10jqka.com.cn/'
            }

            for url in urls_to_try:
                try:
                    print(f"      尝试: {url[:50]}...")
                    response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'lxml')

                    # 同花顺的新闻列表选择器
                    selectors = [
                        '.list-item',
                        '.news-item',
                        'a[href*="/news/"]',
                        '.article-list-item',
                        '#newsList li',
                        '.content-list li'
                    ]

                    news_items = []
                    for selector in selectors:
                        items = soup.select(selector)
                        if items:
                            news_items = items[:max_articles * 2]
                            print(f"      找到 {len(items)} 条，使用选择器: {selector}")
                            break

                    if not news_items:
                        print(f"      未找到新闻列表")
                        continue

                    for item in news_items:
                        # 查找链接和标题
                        if item.name in ['li', 'div']:
                            link_tag = item.find('a', href=True)
                            if link_tag:
                                title = link_tag.get_text(strip=True)
                                href = link_tag.get('href', '')
                            else:
                                continue
                        else:
                            title = item.get_text(strip=True)
                            href = item.get('href', '')

                        if title and href and len(title) > 10:
                            # 处理相对URL
                            if not href.startswith('http'):
                                if href.startswith('//'):
                                    href = 'https:' + href
                                elif href.startswith('/'):
                                    href = 'https://www.10jqka.com.cn' + href
                                else:
                                    href = 'https://www.10jqka.com.cn/' + href

                            # 获取时间标签
                            time_tag = item.find(['span', 'time'], class_=lambda x: x and 'time' in str(x).lower())
                            time_str = time_tag.get_text(strip=True) if time_tag else ""

                            # 获取内容
                            content = self.fetch_full_article(href)
                            if not content or len(content) < 50:
                                content = f"{title} {time_str}".strip()

                            if not content or len(content) < 20:
                                content = title

                            summary = self._generate_summary(title, content)

                            articles.append({
                                'title': title,
                                'url': href,
                                'content': content[:2000],
                                'summary': summary,
                                'source': source_name,
                                'fetched_at': datetime.now().isoformat()
                            })

                            # 达到目标数量后停止
                            if len(articles) >= max_articles:
                                break

                    if articles:
                        print(f"    同花顺成功获取 {len(articles)} 篇")
                        return articles

                except Exception as e:
                    print(f"      同花顺尝试 {url[:40]} 失败: {str(e)[:50]}")
                    continue

        except Exception as e:
            print(f"    同花顺专用方法失败: {str(e)[:80]}")

        return articles

    def _method_china_securities_special(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """中国证券报专用方法 - 优化版"""
        if source_name != 'china_securities':
            return []

        print(f"    中国证券报专用方法...")
        articles = []

        try:
            urls_to_try = [
                "https://www.cs.com.cn/",
                "https://www.cs.com.cn/index.html",
                "https://www.cs.com.cn/news/"
            ]

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }

            for url in urls_to_try:
                try:
                    print(f"      尝试: {url[:50]}...")
                    response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'lxml')

                    # 中国证券报的新闻列表选择器
                    selectors = [
                        '.news-list li',
                        '.news-item',
                        '.article-list li',
                        'ul.news li',
                        '.content-list li',
                        'a[href*="/news/"]',
                        'a[href*="/shtml"]',
                        'a[href*="/html"]'
                    ]

                    news_items = []
                    for selector in selectors:
                        items = soup.select(selector)
                        if items:
                            news_items = items[:max_articles * 3]  # 获取更多以便筛选
                            print(f"      找到 {len(items)} 条，使用选择器: {selector}")
                            break

                    if not news_items:
                        print(f"      未找到新闻列表")
                        continue

                    for item in news_items:
                        # 查找链接和标题
                        if item.name == 'li':
                            link_tag = item.find('a', href=True)
                            if link_tag:
                                title = link_tag.get_text(strip=True)
                                href = link_tag.get('href', '')
                            else:
                                continue
                        elif item.name == 'a':
                            title = item.get_text(strip=True)
                            href = item.get('href', '')
                        else:
                            link_tag = item.find('a', href=True)
                            if link_tag:
                                title = link_tag.get_text(strip=True)
                                href = link_tag.get('href', '')
                            else:
                                continue

                        if title and href and len(title) > 10:
                            # 处理相对URL
                            if not href.startswith('http'):
                                if href.startswith('//'):
                                    href = 'https:' + href
                                elif href.startswith('/'):
                                    href = 'https://www.cs.com.cn' + href
                                else:
                                    href = 'https://www.cs.com.cn/' + href

                            # 获取内容
                            content = self.fetch_full_article(href)
                            if not content or len(content) < 50:
                                # 如果全文获取失败，使用标题
                                content = title

                            if not content or len(content) < 20:
                                continue

                            summary = self._generate_summary(title, content)

                            articles.append({
                                'title': title,
                                'url': href,
                                'content': content[:2000],
                                'summary': summary,
                                'source': source_name,
                                'fetched_at': datetime.now().isoformat()
                            })

                            # 达到目标数量后停止
                            if len(articles) >= max_articles:
                                break

                    if articles:
                        print(f"    中国证券报成功获取 {len(articles)} 篇")
                        return articles

                except Exception as e:
                    print(f"      中国证券报尝试 {url[:40]} 失败: {str(e)[:50]}")
                    continue

        except Exception as e:
            print(f"    中国证券报专用方法失败: {str(e)[:80]}")

        return articles

    def _method_generic(self, source_name: str, max_articles: int, source_config: Dict) -> List[Dict]:
        """通用方法：最后尝试"""
        print(f"    通用方法: 尝试首页抓取...")

        url = source_config.get('url', '')
        if not url:
            return []

        articles = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}

            response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')

            # 通用选择器
            selectors = [
                'a[href*="/doc-"]', 'a[href*="/roll/"]',
                'a[href*="/news/"]', 'a[href*="/article/"]',
                '.news-item a', 'article a', '.post-title a'
            ]

            for selector in selectors:
                items = soup.select(selector)
                for item in items[:max_articles]:
                    href = item.get('href', '')
                    title = item.get_text(strip=True)

                    if title and href and len(title) > 10:
                        if not href.startswith('http'):
                            href = url.rstrip('/') + '/' + href.lstrip('/')

                        content = self.fetch_full_article(href)
                        if content and len(content) > 100:
                            if self.is_english(title):
                                title = self.translate_to_chinese(title)
                                content = self.translate_to_chinese(content)

                            summary = self._generate_summary(title, content)

                            articles.append({
                                'title': title,
                                'url': href,
                                'content': content[:2000],
                                'summary': summary,
                                'source': source_name,
                                'fetched_at': datetime.now().isoformat()
                            })

                    if len(articles) >= max_articles:
                        break

                if articles:
                    break

        except Exception as e:
            print(f"    通用方法失败: {str(e)[:80]}")

        return articles

    def _generate_summary(self, title: str, content: str) -> str:
        """生成简单摘要"""
        sentences = re.split(r'[。\n\r\.!]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        key_sentences = sentences[:2] if len(sentences) >= 2 else sentences

        summary = "【摘要】\n"
        for sent in key_sentences:
            sent = re.sub(r'责任编辑：.*', '', sent)
            sent = re.sub(r'来源：.*', '', sent)
            sent = sent.strip()
            if len(sent) > 80:
                sent = sent[:80] + "..."
            if sent:
                summary += f"{sent}\n"

        return summary.strip()

    def fetch_all_sources(self, max_articles_per_source: int = 5) -> Dict[str, List[Dict]]:
        """从所有配置的源获取新闻"""
        all_articles = {}

        print("=" * 60)
        print(f"开始抓取所有新闻源（每源最多{max_articles_per_source}篇）")
        print("=" * 60)

        total_sources = len(self.sources)
        print(f"配置的源数量: {total_sources}")
        print()

        enabled_sources = {k: v for k, v in self.sources.items() if v.get('enabled', False)}

        print(f"启用的源: {len(enabled_sources)}")
        print()

        for source_name, source_config in enabled_sources.items():
            print(f"[{source_name}]")

            articles = self.fetch_with_retries(source_name, source_config, max_articles_per_source)

            if articles:
                all_articles[source_name] = articles
                print(f"  [OK] 成功: {len(articles)} 篇")
            else:
                all_articles[source_name] = []
                print(f"  [FAIL] 失败: 0 篇")

            print()

        # 保存成功方法
        self.save_success_methods()

        # 统计
        total_articles = sum(len(articles) for articles in all_articles.values())
        successful_sources = sum(1 for articles in all_articles.values() if articles)

        print("=" * 60)
        print(f"抓取完成！")
        print(f"  总源数: {total_sources}")
        print(f"  成功源: {successful_sources}")
        print(f"  总文章数: {total_articles}")
        print("=" * 60)

        return all_articles


def test_one_news():
    """测试：只抓取一条新闻"""
    print("=" * 60)
    print("OpenClaw Skill 测试")
    print("=" * 60)
    print("配置: 只抓取1条新闻\n")

    fetcher = NewsFetcher()

    # 只启用一个源进行测试
    test_source = None
    for source_name, source_config in fetcher.sources.items():
        if source_config.get('enabled', False):
            test_source = source_name
            break

    if not test_source:
        print("错误: 没有启用的新闻源")
        return False

    print(f"测试源: {test_source}\n")

    # 只获取1条
    articles = fetcher.fetch_with_retries(test_source, fetcher.sources[test_source], max_articles=1)

    if not articles:
        print("测试失败: 未获取到新闻")
        return False

    article = articles[0]

    # 发送到Telegram
    print("\n发送到Telegram...")
    message = f"""OpenClaw Skill 测试
{'='*50}

【测试新闻】
来源: {article['source']}
时间: {article['fetched_at'][:16]}

标题: {article['title']}

{article['summary']}

详情: {article['url']}
{'='*50}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, json=data, proxies=PROXIES, timeout=30)
        result = response.json()

        if result.get('ok'):
            print("[成功] 已发送到Telegram!")
            return True
        else:
            print(f"[失败] {result}")
            return False

    except Exception as e:
        print(f"[错误] {e}")
        return False


if __name__ == '__main__':
    # 测试模式：只抓取1条新闻
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        success = test_one_news()
        sys.exit(0 if success else 1)

    # 完整模式：抓取所有源
    else:
        fetcher = NewsFetcher()
        all_articles = fetcher.fetch_all_sources(max_articles_per_source=5)

        # 保存结果
        data_dir = Path(__file__).parent / 'data'
        data_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = data_dir / f'all_sources_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)

        print(f"\n数据已保存: {filename}")
