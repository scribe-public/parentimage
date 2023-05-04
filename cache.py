import os
import json

def empty():
    pass

class Cache():

    def __init__(self):
        pass

    def exists(self):
        pass

    def add(self):
        pass

    def get(self):
        pass

    def flush(self):
        pass


class FileCache(Cache):
    cache = {}
    filename = ""
    get_value_by_key = empty

    def __init__(self, filename, ):
        self.filename = filename
        if(os.path.exists(filename)):
            with open(filename, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def exists(self, key):
        if key in self.cache:
            return True
        else:
            return False

    def add(self, key, value):
        if self.exists(key):
            return
        else:
            self.cache[key] = value
    
    def get(self, key):
        if key in self.cache:
            return(self.cache[key])
        else:
            return None

    def flush(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=4)
