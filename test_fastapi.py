from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import List

app = FastAPI()

@app.post("/test")
def test_endpoint(diagrams: List[dict]):
    return diagrams

client = TestClient(app)
res1 = client.post("/test", json=[{"id": 1}])
res2 = client.post("/test", json={"diagrams": [{"id": 1}]})
print("Array body status:", res1.status_code)
print("Dict body status:", res2.status_code)
