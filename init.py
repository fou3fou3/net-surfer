import json, sqlite3
from sqlite3 import Connection

connection = sqlite3.connect('src/database/net_surfer.db')


# Be sure to run this file before starting the crawler or making any database operations as it cleans the json files
# and initializes database tables

def init_crawled_list(file_name: str = 'src/json_data/crawled_links.json') -> None:
	with open(file_name, 'w') as json_file:
		json.dump({'crawled_links': []}, json_file, indent=4)

def init_seed_list(file_name: str = 'src/json_data/seed_list.json') -> None:
	with open(file_name, 'w') as json_file:
		json.dump({'seed_list': []}, json_file, indent=4)


def init_crawled_links_table(conn: Connection):
	try:
		cursor = conn.cursor()

		cursor.execute('''CREATE TABLE IF NOT EXISTS crawled_pages (
							page_url TEXT PRIMARY KEY,
							page_content TEXT NOT NULL,
							page_title TEXT NOT NULL,
							parent_link TEXT,
							created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
							FOREIGN KEY (parent_link) REFERENCES crawled_pages(page_url)
							);
					  ''')

		conn.commit()

	except Exception as e:
		print(f'Error initializing the crawled_pages table: {e}')


def init_words_table(conn: Connection):
	try:
		cursor = conn.cursor()

		cursor.execute('''CREATE TABLE IF NOT EXISTS word_frequencies (
							page_url TEXT,
							word TEXT NOT NULL,
							frequency INTEGER NOT NULL,
							PRIMARY KEY (page_url, word),
							FOREIGN KEY (page_url) REFERENCES crawled_pages(page_url)
						);
					  ''')

		cursor.execute('''CREATE INDEX IF NOT EXISTS idx_word ON word_frequencies (word);''')

		conn.commit()

	except Exception as e:
		print(f'Error initializing the words_frequencies table: {e}')


def init_robots_table(conn: Connection):
	try:
		cursor = conn.cursor()

		cursor.execute('''CREATE TABLE IF NOT EXISTS robots_txt (
							base_url TEXT PRIMARY KEY,
							robots_text TEXT NOT NULL
							);
					  ''')

		conn.commit()

	except Exception as e:
		print(f'Error initializing the robots_txt table: {e}')


init_json_functions = [init_crawled_list(), init_seed_list()]
init_tables_functions = [init_crawled_links_table(conn=connection), init_words_table(connection),
                         init_words_table(connection)]
