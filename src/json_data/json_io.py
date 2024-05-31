import json

def load_seed_list(file_name: str = 'json_data/seed_list.json') -> list[str]:
	with open(file_name, 'r') as json_file:
		return json.load(json_file)['seed_list']
