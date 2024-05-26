import json
from sqlite3 import Connection

def add_page_to_db(conn: Connection, page_link: str, page_html_content: str, child_links: list[str], parent_link: str = 'NULL',):
    try:
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS crawled_pages (
                            page_link TEXT PRIMARY KEY,
                            page_html_content TEXT NOT NULL,
                            parent_link TEXT,
                            child_links TEXT,
                            FOREIGN KEY (parent_link) REFERENCES crawled_pages(page_link)
                            );
                      ''')

        cursor.execute(''' INSERT INTO crawled_pages (page_link, page_html_content, parent_link, child_links) VALUES (?, ?, ?, ?) ''',
                       (page_link, page_html_content, parent_link, json.dumps(child_links)))

        conn.commit()

        print(f'|- Successfully added {page_link} to the database.')

    except Exception as e:
        print(f'|- Error adding page to the database: {e}')


def fetch_robots_txt(conn: Connection, base_url: str) -> str | None:
    try:
        cursor = conn.cursor()

        cursor.execute('SELECT robots_text FROM robots_txt WHERE base_url = ?', (base_url,))

        result = cursor.fetchone()
        if result:
            print(f'|- Successfully fetched robots.txt of {base_url}')
            return result[0]

        else:
            print(f'|- No robots.txt found in the database for {base_url}')
            return None

    except Exception as e:
        print(f'|- Error fetching robots.txt from the database: {e}')
        return None
def add_robots_txt(conn: Connection, base_url: str, robots_txt: str):
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