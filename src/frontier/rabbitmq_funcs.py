import pika, json

async def add_to_frontier(urls: list[str], parent_url: str, queue_name='frontier'):
	# Connect to RabbitMQ
	connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
	channel = connection.channel()

	# Send links to the queue
	for url in urls:
		channel.basic_publish(exchange='',
							  routing_key=queue_name,
							  body=json.dumps({'url': url, 'parent_url': parent_url}),
							  properties=pika.BasicProperties(
								  delivery_mode=2,  # make message persistent
							  ))

	# Close the connection
	connection.close()


async def fetch_from_frontier(queue_name='frontier', num_urls=5) -> list[dict[str]]:
	# Connect to RabbitMQ
	connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
	channel = connection.channel()

	# Declare a queue
	channel.queue_declare(queue=queue_name, durable=True)

	# Retrieve and acknowledge messages
	urls = []
	for _ in range(num_urls):
		method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=False)
		if method_frame:
			urls.append(json.loads(body.decode()))
			channel.basic_ack(delivery_tag=method_frame.delivery_tag)
		else:
			break

	# Close the connection
	connection.close()

	return urls