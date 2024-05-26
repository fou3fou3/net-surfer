import requests, sqlite3
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, ParseResult
from urllib.robotparser import RobotFileParser
from database.db import *
from json_data.json_io import *


USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'

conn = sqlite3.connect('database/net_surfer.db')

def get_page_data(parent_link: str, html_content: bytes, parsed_parent_link: ParseResult) -> (list[str], str):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_links = []

    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            link = unquote(href)
            parsed_link = urlparse(link)

            if not parsed_link.scheme in ['http', 'https']:
                if not list(link)[0] == '#':
                    if list(link)[0] == '/':
                        link = f"{parsed_parent_link.scheme}://{parsed_parent_link.netloc}{link}"
                    else:
                        link = f"{parsed_parent_link.scheme}://{parsed_parent_link.netloc}/{link}"

                    page_links.append(link)
                    print(f'\t|- Fetched {link}')

            else:
                page_links.append(link)
                print(f'\t|- Fetched {link}')

    return page_links, html_content.decode('utf-8')

def main(allowed_urls: tuple[str] = (), robots_txt: bool = False):
    crawled_links = load_crawled_list()
    seed_set = load_seed_set()
    if robots_txt:
        rp = RobotFileParser()

    while seed_set:
        seed_list = list(seed_set)

        for index, parent_link in enumerate(seed_list):
            print(f'|- Crawling through {parent_link}.')
            try:
                resp = requests.get(parent_link, headers={'User-Agent': USER_AGENT})
                if resp.status_code == 200:
                    parsed_parent_link = urlparse(parent_link)
                    base_url = f'{parsed_parent_link.scheme}://{parsed_parent_link.netloc}'
                    links, html_content = get_page_data(parent_link, resp.content, parsed_parent_link)

                    if robots_txt:
                        base_url_robots = fetch_robots_txt(conn, base_url)
                        if not base_url_robots:
                            base_url_robots = requests.get(f'{base_url}/robots.txt').text
                            add_robots_txt(conn, base_url, base_url_robots)
                        rp.parse(base_url_robots.splitlines())

                    links = [link for link in links
                             if link not in [crawled_links + seed_list]
                             and (True if not allowed_urls else any(link.startswith(allowed_url) for allowed_url in allowed_urls))
                             and (True if not robots_txt else rp.can_fetch(USER_AGENT, link))]

                    seed_set.update(links)

                    if index > 0:
                        add_page_to_db(conn, parent_link, html_content, links, seed_list[index - 1])
                    else:
                        add_page_to_db(conn, parent_link, html_content, links)

                    print(f'|- Done crawling through {parent_link}.\n\n')

                else:
                    print(f'|- Problem crawling through {parent_link}, {resp.status_code}\n\n')

            except requests.exceptions.RequestException as e:
                print(f'|- There was an error sending the request: {e}\n\n')

            seed_set.remove(parent_link)
            crawled_links.append(parent_link)

            append_crawled_list(crawled_links)
            append_seed_set(seed_set)


if __name__ == '__main__':
    main()