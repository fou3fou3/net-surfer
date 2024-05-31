from sqlite3 import Connection


async def add_page_to_db(conn: Connection, page_url: str, page_content: str, page_title: str,
                         parent_link: str = 'NULL'):
    try:
        cursor = conn.cursor()

        if not page_title:
            page_title = 'NULL'

        cursor.execute(
            ''' INSERT INTO crawled_pages (page_url, page_content, page_title, parent_link) VALUES (?, ?, ?, ?) ''',
            (page_url, page_content, page_title, parent_link))

        conn.commit()

        print(f'|- Successfully added {page_url} to the database.')

    except Exception as e:
        print(f"|- Error adding page {page_url} to the database: {e}")


async def add_words_to_db(conn: Connection, page_url: str, words: list[tuple[str, int]]):
    try:
        cursor = conn.cursor()

        for word, freq in words:
            try:
                # Try to update the frequency if the record exists
                cursor.execute(
                    '''UPDATE word_frequencies SET frequency = frequency + ? 
                       WHERE page_url = ? AND word = ?''',
                    (freq, page_url, word)
                )

                if cursor.rowcount == 0:
                    # If no rows were updated, insert the new word with its frequency
                    cursor.execute(
                        '''INSERT INTO word_frequencies (page_url, word, frequency) 
                           VALUES (?, ?, ?)''',
                        (page_url, word, freq)
                    )
            except Exception as e:
                print(f'|- Error updating word frequency: {e}')

        conn.commit()

    except Exception as e:
        print(f'|- Error adding word to the database: {e}')