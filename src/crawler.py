import requests, sqlite3, aiohttp, asyncio, nltk
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, ParseResult
from urllib.robotparser import RobotFileParser
from database.db import *
from collections import Counter
from json_data.json_io import *
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize



class Crawler:
    def __init__(self, allowed_paths: tuple[str] = (), respect_robots: bool = False, pages_per_time: int = 15,
                 request_delay: float = 2) -> None:
        nltk.download('punkt')
        nltk.download('stopwords')

        self.stop_words = set(stopwords.words('english'))
        self.allowed_paths = allowed_paths
        self.respect_robots = respect_robots
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        self.sqlite3_conn = sqlite3.connect('database/net_surfer.db')
        self.crawled_urls = load_crawled_list()
        self.seed_set = load_seed_set()
        self.seed_list = []
        self.page_per_time = pages_per_time
        self.sliced_seed_list = []
        self.request_delay = request_delay

    async def dump_data_to_db(self, page_url: str, page_content: str, page_title: str, index: int,
                              words: dict[str: int]):
        if index > 0:
            await add_page_to_db(self.sqlite3_conn, page_url, page_content, page_title,
                           self.sliced_seed_list[index - 1])
        else:
            await add_page_to_db(self.sqlite3_conn, page_url, page_content, page_title)

        await add_words_to_db(self.sqlite3_conn, page_url, words)

    async def scrape_page_data(self, html_content: bytes, parsed_page_url: ParseResult) -> (list[str], str, str, str):
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text()
        words = [word for word in word_tokenize(page_text) if word.isalnum() and word.lower() not in self.stop_words]
        words = [(word, freq) for word, freq in Counter(words).items()]

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

    async def filter_child_urls(self, seen_urls: set[str], urls: list[str], rp: RobotFileParser) -> list[str]:
        filtred_urls = []
        for url in urls:
            if url not in seen_urls:
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

    async def crawl_page(self, page_url: str, index: int, session: aiohttp.ClientSession) -> None:
        print(f'|- Crawling through {page_url}')
        try:
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

                    seen_urls = set(self.crawled_urls) | self.seed_set
                    child_urls = await self.filter_child_urls(seen_urls, child_urls, rp)

                    await asyncio.sleep(self.request_delay)

                    self.seed_set.update(child_urls)

                    await self.dump_data_to_db(page_url, page_content, page_title, index, page_words)

                    print(f'|- Done crawling through {page_url}.\n\n')

                else:
                    print(f'|- Problem crawling through {page_url}, {resp.status}\n\n')

        except requests.exceptions.RequestException as e:
            print(f'|- There was an error sending the request: {e}\n\n')
        except Exception as e:
            print(f'|- There was an error handeling the request: {e}')

    async def crawl_pages(self) -> None:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for index, page_url in enumerate(self.sliced_seed_list):
                tasks.append(asyncio.create_task(self.crawl_page(page_url, index, session)))
            await asyncio.gather(*tasks)

        for page_url in self.sliced_seed_list:
            self.seed_set.remove(page_url)
            self.crawled_urls.append(page_url)

        # update crawled list one time because we are appending and that doesn't affect the overal list
        update_crawled_list(self.crawled_urls)
        # update the set here because we removed all crawled urls + added child links from them
        update_seed_set(self.seed_set)

    async def run(self) -> None:
        while self.seed_set:
            self.seed_list = list(self.seed_set)

            start = 0
            while start < len(self.seed_list):
                end = start + self.page_per_time
                self.sliced_seed_list = self.seed_list[start: end]
                await self.crawl_pages()
                start = end