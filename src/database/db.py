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