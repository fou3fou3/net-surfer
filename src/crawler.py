import requests, sqlite3
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, ParseResult
from urllib.robotparser import RobotFileParser
from database.db import *
from json_data.json_io import *


class Crawler:
    def __init__(self, allowed_paths: tuple[str] = (), respect_robots: bool = False):
        self.allowed_paths = allowed_paths
        self.respect_robots = respect_robots
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        self.sqlite3_conn = sqlite3.connect('database/net_surfer.db')
        self.rp = RobotFileParser()

    def scrape_page_data(self, html_content: bytes, parsed_parent_url: ParseResult) -> (list[str], str):
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

    def filter_child_urls(self, seen_urls: list[str], urls: list[str]) -> list[str]:
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

    def crawl(self, parent_url: str, crawled_urls: list[str], seed_list: list[str], seed_set: set[str],
              index: int) -> None:
        print(f'|- Crawling through {parent_url}')

        try:
            resp = requests.get(parent_url, headers={'User-Agent': self.user_agent})
            if resp.status_code == 200:
                parsed_parent_url = urlparse(parent_url)
                base_url = f'{parsed_parent_url.scheme}://{parsed_parent_url.netloc}'
                child_urls, html_content = self.scrape_page_data(resp.content, parsed_parent_url)

                if self.respect_robots:
                    base_url_robots = fetch_robots_txt(self.sqlite3_conn, base_url)
                    if not base_url_robots:
                        base_url_robots = requests.get(f'{base_url}/robots.txt').text
                        add_robots_txt(self.sqlite3_conn, base_url, base_url_robots)

                    self.rp.parse(base_url_robots.splitlines())

                seen_urls = crawled_urls + seed_list
                child_urls = self.filter_child_urls(seen_urls, child_urls)

                seed_set.update(child_urls)

                if index > 0:
                    add_page_to_db(self.sqlite3_conn, parent_url, html_content, child_urls, seed_list[index - 1])
                else:
                    add_page_to_db(self.sqlite3_conn, parent_url, html_content, child_urls)

                print(f'|- Done crawling through {parent_url}.\n\n')

            else:
                print(f'|- Problem crawling through {parent_url}, {resp.status_code}\n\n')

        except requests.exceptions.RequestException as e:
            print(f'|- There was an error sending the request: {e}\n\n')

    def run(self):
        crawled_urls = load_crawled_list()
        seed_set = load_seed_set()

        while seed_set:
            seed_list = list(seed_set)

            for index, parent_url in enumerate(seed_list):
                self.crawl(parent_url, crawled_urls, seed_list, seed_set, index)

                seed_set.remove(parent_url)
                crawled_urls.append(parent_url)
                append_crawled_list(crawled_urls)
                append_seed_set(seed_set)
