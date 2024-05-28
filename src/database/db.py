from sqlite3 import Connection


async def add_page_to_db(conn: Connection, page_url: str, page_content: str, page_title: str,
                         parent_link: str = 'NULL'):
    try:
        cursor = conn.cursor()

        if not page_title:
            page_title = 'NULL'

        cursor.execute('''CREATE TABLE IF NOT EXISTS crawled_pages (
                            page_url TEXT PRIMARY KEY,
                            page_content TEXT NOT NULL,
                            page_title TEXT NOT NULL,
                            parent_link TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (parent_link) REFERENCES crawled_pages(page_url)
                            );
                      ''')

        cursor.execute(
            ''' INSERT INTO crawled_pages (page_url, page_content, page_title, parent_link) VALUES (?, ?, ?, ?) ''',
            (page_url, page_content, page_title, parent_link))

        conn.commit()

        print(f'|- Successfully added {page_url} to the database.')

    except Exception as e:
        print(f'|- Error adding page to the database: {e}')


async def add_words_to_db(conn: Connection, page_url: str, words: list[tuple[str, int]]):
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

        cursor.executemany(
            ''' INSERT INTO word_frequencies (page_url, word, frequency) VALUES (?, ?, ?) ''',
	        [(page_url, word, freq) for word, freq in words])

        conn.commit()

    except Exception as e:
        print(f'|- Error adding word to the database: {e}')


async def fetch_robots_txt(conn: Connection, base_url: str) -> str | None:
    try:
        cursor = conn.cursor()

        cursor.execute('SELECT robots_text FROM robots_txt WHERE base_url = ?', (base_url,))

        result = cursor.fetchone()
        if result:
            return result[0]

        print(f'|- No robots.txt found in the database for {base_url}')
        return None

    except Exception as e:
        print(f'|- Error fetching robots.txt from the database: {e}')
        return None


async def add_robots_txt(conn: Connection, base_url: str, robots_txt: str):
    try:
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS robots_txt (
                            base_url TEXT PRIMARY KEY,
                            robots_text TEXT NOT NULL
                            );
                      ''')

        cursor.execute(''' INSERT INTO robots_txt (base_url, robots_text) VALUES (?, ?) ''',
                       (base_url, robots_txt))

        conn.commit()

        print(f'|- Successfully added robots.txt of {base_url} to the database.')

    except Exception as e:
        print(f'|- Error adding robots.txt to the database: {e}')