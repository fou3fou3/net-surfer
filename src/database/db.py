import asyncpg
from asyncpg import Connection

async def add_page_to_db(conn: Connection, page_url: str, page_content: str, page_title: str, parent_link: str = None):
	try:
		if parent_link:
			await conn.execute(
				'''INSERT INTO crawled_pages (page_url, page_content, page_title, parent_link) VALUES ($1, $2, $3, $4)''',
				page_url, page_content, page_title, parent_link)
		else:
			await conn.execute(
				'''INSERT INTO crawled_pages (page_url, page_content, page_title) VALUES ($1, $2, $3)''',
				page_url, page_content, page_title)
		
	except Exception as e:
		print(f"\t|- Error adding page {page_url} to the database: {e}")
		
		
async def add_words_to_db(conn: asyncpg.Connection, page_url: str, words: list[tuple[str, int]]):
	try:
		async with conn.transaction():
			for word, freq in words:
				try:
					# Try to update the frequency if the record exists
					update_query = '''
						UPDATE word_frequencies
						SET frequency = word_frequencies.frequency + $1
						WHERE page_url = $2 AND word = $3
					'''
					res = await conn.execute(update_query, freq, page_url, word)
					
					if res == 'UPDATE 0':
						# If no rows were updated, insert the new word with its frequency
						insert_query = '''
							INSERT INTO word_frequencies (page_url, word, frequency)
							VALUES ($1, $2, $3)
						'''
						await conn.execute(insert_query, page_url, word, freq)
				
				except Exception as e:
					print(f'|- Error updating word frequency: {e}')
			
	except Exception as e:
		print(f'\t|- Error adding word to the database: {e}')