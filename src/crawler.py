import requests, sqlite3, aiohttp, asyncio, nltk, re, os
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, ParseResult
from urllib.robotparser import RobotFileParser
from database.db import *
from crawled_urls.redis_funcs import *
from frontier.rabbitmq_funcs import *
from collections import Counter
from json_data.json_io import *
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize



class Crawler:
    def __init__(self, allowed_paths: tuple[str] = (), respect_robots: bool = False, pages_per_time: int = 5,
                 request_delay: float = 1, crawl_depth: int = None, threads: int = 1) -> None:
        nltk.download('punkt')
        nltk.download('stopwords')

        self.stop_words = set(stopwords.words('english'))
        self.allowed_paths = allowed_paths
        self.respect_robots = respect_robots
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        self.sqlite3_conn = sqlite3.connect('database/net_surfer.db')
        self.page_per_time = pages_per_time
        self.request_delay = request_delay
        self.crawl_depth = crawl_depth
        self.crawl_counter = 0
        self.threads = threads

    async def dump_data_to_db(self, page_url: str, page_content: str, page_title: str, words: dict[str: int], parent_url: str):
        if parent_url != 'NULL':
            await add_page_to_db(self.sqlite3_conn, page_url, page_content, page_title, parent_url)
        else:
            await add_page_to_db(self.sqlite3_conn, page_url, page_content, page_title)

        await add_words_to_db(self.sqlite3_conn, page_url, words)

    async def scrape_page_data(self, html_content: bytes, parsed_page_url: ParseResult) -> (list[str], str, str, str):
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = re.sub(r'\s+', ' ', soup.body.get_text(separator=' ')).strip()

        words = [word for word in word_tokenize(page_text) if word.isalnum() and word.lower() not in self.stop_words]
        words = [(word.lower(), freq) for word, freq in Counter(words).items()]

        page_urls = []

        for url in soup.find_all('a'):
            href = url.get('href')
            if href:
                url = unquote(href)
                parsed_url = urlparse(url)

                if not parsed_url.scheme in ['http', 'https']:
                    if not list(url)[0] == '#':
                        if list(url)[0] == '/':
                            url = f"{parsed_page_url.scheme}://{parsed_page_url.netloc}{url}"
                        else:
                            url = f"{parsed_page_url.scheme}://{parsed_page_url.netloc}/{url}"

                        page_urls.append(url)
                        print(f'\t|- Fetched {url}')

                else:
                    page_urls.append(url)
                    print(f'\t|- Fetched {url}')

        return page_urls, page_text, soup.title.string, words

    async def filter_child_urls(self, urls: list[str], rp: RobotFileParser) -> list[str]:
        filtred_urls = []
        crawled_urls = get_all_crawled_urls()

        for url in urls:
            if url not in crawled_urls:
                if not self.allowed_paths:
                    path_permit = True
                else:
                    path_permit = any(url.startswith(allowed_url) for allowed_url in self.allowed_paths)

                if not self.respect_robots:
                    robots_permit = True
                else:
                    robots_permit = rp.can_fetch(self.user_agent, url)

                if path_permit and robots_permit:
                    filtred_urls.append(url)

        return filtred_urls

    async def crawl_page(self, page_url: str, parent_url: str, session: aiohttp.ClientSession) -> None:
        print(f'|- Crawling through {page_url}')
        try:
            crawled_urls = get_all_crawled_urls()

            if page_url in crawled_urls:
                raise Exception('Url has been crawled')

            async with session.get(page_url, headers={'User-Agent': self.user_agent}) as resp:
                if resp.status == 200:
                    rp = RobotFileParser()
                    parsed_page_url = urlparse(page_url)
                    base_url = f'{parsed_page_url.scheme}://{parsed_page_url.netloc}'
                    child_urls, page_content, page_title, page_words = await self.scrape_page_data(await resp.read(),
                                                                                                   parsed_page_url)

                    if self.respect_robots:
                        base_url_robots = await fetch_robots_txt(self.sqlite3_conn, base_url)
                        if not base_url_robots:
                            async with session.get(f'{base_url}/robots.txt') as robots_resp:
                                base_url_robots = await robots_resp.text()
                                await add_robots_txt(self.sqlite3_conn, base_url, base_url_robots)

                        rp.parse(base_url_robots.splitlines())

                    child_urls = await self.filter_child_urls(child_urls, rp)

                    await asyncio.sleep(self.request_delay)

                    await add_to_frontier(child_urls, page_url)

                    await self.dump_data_to_db(page_url, page_content, page_title, page_words, parent_url)

                    add_crawled_url(page_url)

                    print(f'|- Done crawling through {page_url}.\n\n')

                    if self.crawl_depth:
                        self.crawl_counter += 1

                        if self.crawl_depth <= self.crawl_counter:
                            print(f'Reached maximum crawl depth ({self.crawl_depth}) exiting .. ({page_url})')
                            os._exit(0)

                else:
                    print(f'|- Problem crawling through {page_url}, {resp.status}\n\n')

        except requests.exceptions.RequestException as e:
            print(f'|- There was an error sending the request: {e}\n\n')
        except Exception as e:
            print(f'|- There was an error handeling the request: {e}')

    async def crawl_pages(self) -> None:
        frontier = await fetch_from_frontier(num_urls=self.page_per_time)
        while frontier:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for url_data in frontier:
                    tasks.append(asyncio.create_task(self.crawl_page(url_data['url'], url_data['parent_url'], session)))
                await asyncio.gather(*tasks)

            frontier = await fetch_from_frontier(num_urls=self.page_per_time)

    async def run(self) -> None:
        seed_list = load_seed_list()
        await add_to_frontier(seed_list, 'NULL')

        await self.crawl_pages()