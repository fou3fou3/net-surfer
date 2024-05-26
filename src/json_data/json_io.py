import json

def load_seed_list(file_name: str = 'json_data/seed_list.json') -> set[str]:
    with open(file_name, 'r') as json_file:
        return set(json.load(json_file)['seed_list'])

def append_seed_list(updated_seed_list: set[str], file_name: str = 'json_data/seed_list.json') -> None:
    with open(file_name, 'w') as json_file:
        json.dump({'seed_list': list(updated_seed_list)}, json_file, indent=4)

def load_crawled_list(file_name: str = 'json_data/crawled_links.json') -> list[str]:
    with open(file_name, 'r') as json_file:
        return json.load(json_file)['crawled_links']

def append_crawled_list(updated_seed_list: list[str], file_name: str = 'json_data/crawled_links.json') -> None:
    with open(file_name, 'w') as json_file:
        json.dump({'crawled_links': updated_seed_list}, json_file, indent=4)