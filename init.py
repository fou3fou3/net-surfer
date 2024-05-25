import json

def init_crawled_list(file_name: str = 'src/json_data/crawled_links.json') -> None:
    with open(file_name, 'w') as json_file:
        json.dump({'crawled_links': []}, json_file, indent=4)

def init_seed_list(file_name: str = 'src/json_data/seed_list.json') -> None:
    with open(file_name, 'w') as json_file:
        json.dump({'seed_list': []}, json_file, indent=4)


init_seed_list()
init_crawled_list()