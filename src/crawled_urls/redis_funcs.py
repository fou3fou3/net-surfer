import redis


def add_crawled_url(link: str, list_name: str = 'crawled_urls'):
	try:
		conn = redis.Redis(host='localhost', port=6379, db=0)
		conn.lpush(list_name, link)
	except Exception as e:
		print(f'There was an error adding the crawled url : {e}')


def get_all_crawled_urls(list_name: str = 'crawled_urls') -> list[str]:
	try:
		conn = redis.Redis(host='localhost', port=6379, db=0)

		link_count = conn.llen(list_name)
		links = []

		for idx in range(link_count):
			link = conn.lindex(list_name, idx).decode('utf-8')
			links.append(link)

		return links

	except Exception as e:
		print(f'There was an error fetching the crawled urls list: {e}')
