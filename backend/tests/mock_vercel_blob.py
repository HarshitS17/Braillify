import json

_store = {}

def put(key, data, **kwargs):
    _store[key] = data
    return {"url": f"https://mock.blob.vercel-storage.com/{key}"}

class MockResponse:
    def __init__(self, data):
        self._data = data
    def read(self):
        return self._data

def get(key, **kwargs):
    if key in _store:
        return MockResponse(_store[key])
    return None

def delete(key, **kwargs):
    if isinstance(key, list):
        for k in key:
            if k.startswith("https://mock.blob.vercel-storage.com/"):
                k = k.replace("https://mock.blob.vercel-storage.com/", "")
            _store.pop(k, None)
    else:
        if key.startswith("https://mock.blob.vercel-storage.com/"):
            key = key.replace("https://mock.blob.vercel-storage.com/", "")
        _store.pop(key, None)

class MockListResponse:
    def __init__(self, blobs):
        self.blobs = blobs
    
    def get(self, key, default=None):
        if key == "blobs":
            return self.blobs
        return default

def list_objects(prefix="", **kwargs):
    blobs = []
    for k in _store.keys():
        if k.startswith(prefix):
            blobs.append({"pathname": k, "url": f"https://mock.blob.vercel-storage.com/{k}"})
    return MockListResponse(blobs)

def head(key, **kwargs):
    if key not in _store:
        raise Exception("Not found")
    return True

def clear():
    _store.clear()
