import json


class _Properties(dict):
    def __init__(self, path_to_file: str):
        with open(path_to_file, 'r', encoding='utf-8') as f:
            props = json.load(f)

        super().__init__(**props)


CONFIG = _Properties('data/config.json')
DEFAULT = _Properties('data/default.json')

DEFAULT['color'] = int(DEFAULT['color'], 16)
