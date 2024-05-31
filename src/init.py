import json, redis, pika, asyncpg, asyncio, dotenv, os
from asyncpg import Connection

# Be sure to run this file before starting the crawler or making any database operations as it cleans the json files
# and initializes database tables

dotenv.load_dotenv()

def init_seed_list(file_name: str = 'src/json_data/seed_list.json') -> None:
	with open(file_name, 'w') as json_file:
		json.dump({'seed_list': []}, json_file, indent=4)


async def create_tables(conn: Connection):
	# Create the crawled_pages table
	await conn.execute('''
		CREATE TABLE IF NOT EXISTS crawled_pages (
			page_url TEXT PRIMARY KEY,
			page_content TEXT NOT NULL,
			page_title TEXT NOT NULL,
			parent_link TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (parent_link) REFERENCES crawled_pages(page_url)
		);
	''')
	await conn.execute('CREATE INDEX IF NOT EXISTS idx_page_url ON crawled_pages(page_url);')

	# Create the word_frequencies table
	await conn.execute('''
		CREATE TABLE IF NOT EXISTS word_frequencies (
			page_url TEXT,
			word TEXT NOT NULL,
			frequency INTEGER NOT NULL,
			PRIMARY KEY (page_url, word),
			FOREIGN KEY (page_url) REFERENCES crawled_pages(page_url)
		);
	''')
	await conn.execute('CREATE INDEX IF NOT EXISTS idx_word ON word_frequencies(word);')

async def clear_tables(conn: Connection):
	# Clear the crawled_pages table
	await conn.execute('TRUNCATE TABLE crawled_pages;')

	# Clear the word_frequencies table
	await conn.execute('TRUNCATE TABLE word_frequencies;')


def clear_redis_db(list_name: str = 'crawled_urls'):
	try:
		conn = redis.Redis(host='localhost', port=6379, db=0)
		conn.flushdb()
		conn.delete(list_name)
	except Exception as e:
		print(f'There was an error clearing {list_name}: {e}')

def create_crawled_urls(list_name: str = 'crawled_urls'):
	try:
		conn = redis.Redis(host='localhost', port=6379, db=0)
		conn.rpush(list_name, '')

	except Exception as e:
		print(f'There was an error creating the list: {e}')


def init_frontier(queue_name='frontier'):
	try:
		# Connect to RabbitMQ
		conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
		channel = conn.channel()

		# Declare the queue to ensure it exists
		channel.queue_declare(queue=queue_name, durable=True)

		# Purge the queue
		channel.queue_purge(queue=queue_name)
		print(f'Queue "{queue_name}" cleared successfully')

		# Close the connection
		conn.close()
	except pika.exceptions.ChannelClosedByBroker as e:
		print(f"Error clearing queue: {e}")

async def main():
	# Initialize and clear the seed list
	init_seed_list()
	print('Initizalied seed list')
	
	# Establish a connection to PostgreSQL using asyncpg
	conn = await asyncpg.connect(f'postgresql://{os.getenv("DB_USR")}:{os.getenv("DB_PASSWD")}@localhost:5432/net_surfer')

	# Create tables
	await create_tables(conn)
	print('Tables created successfully')

	# Clear tables (optional)
	await clear_tables(conn)
	print('Tables cleared successfully')

	# Close the connection
	await conn.close()
	
	# init redis
	clear_redis_db()
	print('Cleared redis completely')
	
	create_crawled_urls()
	print('Created crawled urls redis list')
 
	init_frontier()
	print('Initialized frontier succesfully')

if __name__ == "__main__":
	asyncio.run(main())