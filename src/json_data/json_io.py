import json

def load_seed_set(file_name: str = 'json_data/seed_list.json') -> set[str]:
    with open(file_name, 'r') as json_file:
        return set(json.load(json_file)['seed_list'])

def update_seed_set(updated_seed_list: set[str], file_name: str = 'json_data/seed_list.json') -> None:
    with open(file_name, 'w') as json_file:
        json.dump({'seed_list': list(updated_seed_list)}, json_file, indent=4)