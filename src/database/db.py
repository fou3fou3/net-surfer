import sqlite3
from sqlite3 import Connection

def add_page_to_db(conn: Connection, page_link: str, page_html_content: str, db_name: str = 'net_surfer.db'):
    try:
        cursor = conn.cursor()

        cursor.execute(''' CREATE TABLE IF NOT EXISTS crawled_pages (
                           page_link TEXT PRIMARY KEY,
                           page_html_content TEXT NOT NULL)
        ''')

        cursor.execute(''' INSERT INTO web_pages (pagelink, page_html_content) VALUES (?, ?) ''', (page_link, page_html_content))
        conn.commit()

    except Exception as e:
        print(f'Error adding page to the database: {e}')
