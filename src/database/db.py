from sqlite3 import Connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def add_page_to_db(conn: Connection, page_link: str, page_html_content: str):
    try:
        cursor = conn.cursor()

        cursor.execute(''' CREATE TABLE IF NOT EXISTS crawled_pages (
                           page_link TEXT PRIMARY KEY,
                           page_html_content TEXT NOT NULL)
        ''')

        cursor.execute(''' INSERT INTO crawled_pages (page_link, page_html_content) VALUES (?, ?) ''', (page_link, page_html_content))
        conn.commit()

        logging.info(f'Successfully added {page_link} to the database .')

    except Exception as e:
        logging.warning(f'Error adding page to the database: {e}')
