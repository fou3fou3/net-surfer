import requests, logging, sqlite3, re
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse
from database.db import add_page_to_db
from json_data.json_io import *


USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'

conn = sqlite3.connect('database/net_surfer.db')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_page_data(parent_link: str, html_content: bytes) -> (list[str], str):
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
                    link = f"{parsed_parent_link.scheme}://{parsed_parent_link.netloc}/{link}"
                    page_links.append(re.sub(r'(?<!:)//+', '/', link))
                    logging.info(f'Fetched {link} from {parent_link}.')
            else:
                page_links.append(link)
                logging.info(f'Fetched {link} from {parent_link}.')

    return page_links, html_content.decode('utf-8')

def main():
    crawled_links = load_crawled_list()
    seed_list = load_seed_list()

    while seed_list:
        for parent_link in list(seed_list):
            logging.info(f'Crawling through {parent_link}.')
            seed_list.remove(parent_link)

            try:
                resp = requests.get(parent_link, headers={'User-Agent': USER_AGENT})
                if resp.status_code == 200:
                    links, html_content = get_page_data(parent_link, resp.content)
                    links = [link for link in links if link not in crawled_links + list(seed_list)]

                    add_page_to_db(conn, parent_link, html_content)

                    logging.info(f'Done crawling through {parent_link}.')

                    seed_list.update(links)
                    crawled_links.append(parent_link)

                    append_crawled_list(crawled_links)
                    append_seed_list(seed_list)

                else:
                    logging.warning(f'Problem crawling through {parent_link}, canceling.')

            except requests.exceptions.RequestException as e:
                logging.warning(f'There was an error sending the request: {e}')



if __name__ == '__main__':
    main()