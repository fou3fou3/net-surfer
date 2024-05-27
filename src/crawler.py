import requests, sqlite3, aiohttp, asyncio
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, ParseResult
from urllib.robotparser import RobotFileParser
from database.db import *
from json_data.json_io import *


class Crawler:
    def __init__(self, allowed_paths: tuple[str] = (), respect_robots: bool = False, pages_per_time: int = 10,
                 request_delay: int = 2) -> None:
        self.allowed_paths = allowed_paths
        self.respect_robots = respect_robots
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        self.sqlite3_conn = sqlite3.connect('database/net_surfer.db')
        self.rp = RobotFileParser()
        self.crawled_urls = load_crawled_list()
        self.seed_set = load_seed_set()
        self.seed_list = []
        self.page_per_time = pages_per_time
        self.sliced_seed_list = []
        self.request_delay = request_delay

    async def scrape_page_data(self, html_content: bytes, parsed_parent_url: ParseResult) -> [list[str], str]:
        soup = BeautifulSoup(html_content, 'html.parser')
        page_urls = []

        for url in soup.find_all('a'):
            href = url.get('href')
            if href:
                url = unquote(href)
                parsed_url = urlparse(url)

                if not parsed_url.scheme in ['http', 'https']:
                    if not list(url)[0] == '#':
                        if list(url)[0] == '/':
                            url = f"{parsed_parent_url.scheme}://{parsed_parent_url.netloc}{url}"
                        else:
                            url = f"{parsed_parent_url.scheme}://{parsed_parent_url.netloc}/{url}"

                        page_urls.append(url)
                        print(f'\t|- Fetched {url}')

                else:
                    page_urls.append(url)
                    print(f'\t|- Fetched {url}')

        return page_urls, html_content.decode('utf-8', errors='ignore')

    async def filter_child_urls(self, seen_urls: set[str], urls: list[str]) -> list[str]:
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
                    robots_permit = self.rp.can_fetch(self.user_agent, url)

                if path_permit and robots_permit:
                    filtred_urls.append(url)

        return filtred_urls

    async def crawl_page(self, parent_url: str, index: int, session: aiohttp.ClientSession) -> None:
        print(f'|- Crawling through {parent_url}')

        try:
            async with session.get(parent_url, headers={'User-Agent': self.user_agent}) as resp:
                if resp.status == 200:
                    await asyncio.sleep(self.request_delay)
                    parsed_parent_url = urlparse(parent_url)
                    base_url = f'{parsed_parent_url.scheme}://{parsed_parent_url.netloc}'
                    child_urls, html_content = await self.scrape_page_data(await resp.read(), parsed_parent_url)

                    if self.respect_robots:
                        base_url_robots = fetch_robots_txt(self.sqlite3_conn, base_url)
                        if not base_url_robots:
                            async with session.get(f'{base_url}/robots.txt') as robots_resp:
                                base_url_robots = await robots_resp.text()
                                add_robots_txt(self.sqlite3_conn, base_url, base_url_robots)

                        self.rp.parse(base_url_robots.splitlines())

                    seen_urls = set(self.crawled_urls) | self.seed_set
                    child_urls = await self.filter_child_urls(seen_urls, child_urls)

                    self.seed_set.update(child_urls)

                    if index > 0:
                        add_page_to_db(self.sqlite3_conn, parent_url, html_content, child_urls,
                                       self.sliced_seed_list[index - 1])
                    else:
                        add_page_to_db(self.sqlite3_conn, parent_url, html_content, child_urls)

                    print(f'|- Done crawling through {parent_url}.\n\n')

                else:
                    print(f'|- Problem crawling through {parent_url}, {resp.status}\n\n')

        except requests.exceptions.RequestException as e:
            print(f'|- There was an error sending the request: {e}\n\n')

    async def crawl_pages(self) -> None:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for index, parent_url in enumerate(self.sliced_seed_list):
                tasks.append(asyncio.create_task(self.crawl_page(parent_url, index, session)))
            await asyncio.gather(*tasks)

        for parent_url in self.sliced_seed_list:
            self.seed_set.remove(parent_url)
            self.crawled_urls.append(parent_url)

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