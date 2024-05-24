import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse
import logging

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_seed_list(file_name: str = 'seed_list.json') -> set[str]:
    with open(file_name, 'r') as json_file:
        return set(json.load(json_file)['seed_list'])

def append_seed_list(updated_seed_list: set[str], file_name: str = 'seed_list.json') -> None:
    with open(file_name, 'w') as json_file:
        json.dump({'seed_list': list(updated_seed_list)}, json_file, indent=4)

def load_crawled_list(file_name: str = 'crawled_links_list.json') -> list[str]:
    with open(file_name, 'r') as json_file:
        return json.load(json_file)['crawled_links']

def append_crawled_list(updated_seed_list: list[str], file_name: str = 'crawled_links_list.json') -> None:
    with open(file_name, 'w') as json_file:
        json.dump({'crawled_links': updated_seed_list}, json_file, indent=4)

def get_page_data(parent_link: str, html_content: bytes) -> list[str]:
    soup = BeautifulSoup(html_content, 'html.parser')
    page_links = []
    parsed_parent_link = urlparse(parent_link)

    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            link = unquote(href)
            parsed_link = urlparse(link)

            if not parsed_link.scheme in ['http', 'https']:
                if not list(link)[0] == '#':
                    link = f"{parsed_parent_link.scheme}://{parsed_parent_link.netloc}{link}"
                    page_links.append(link)
                    logging.info(f'Fetched {link} from {parent_link}.')
            else:
                page_links.append(link)
                logging.info(f'Fetched {link} from {parent_link}.')

    return page_links

def main():
    crawled_links = load_crawled_list()
    seed_list = load_seed_list()

    while True:
        for parent_link in list(seed_list):
            logging.info(f'Crawling through {parent_link}.')
            seed_list.remove(parent_link)

            resp = requests.get(parent_link, headers={'User-Agent': USER_AGENT})
            if resp.status_code == 200:
                links = [link for link in get_page_data(parent_link, resp.content) if link not in crawled_links + list(seed_list)]
                seed_list.update(links)
                crawled_links.append(parent_link)
                append_crawled_list(crawled_links)
                append_seed_list(seed_list)

                logging.info(f'Done crawling through {parent_link}.')
            else:
                logging.warning(f'Problem crawling through {parent_link}, canceling.')

if __name__ == '__main__':
    main()