import httpx
import os

# Unset proxy for localhost
os.environ["NO_PROXY"] = "*"
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

API_BASE = "http://127.0.0.1:8000/api"
client = httpx.Client()

# 1. Create project
res = client.post(f"{API_BASE}/projects", json={"name": "Test Project", "description": "Testing pipeline"})
print("Create project:", res.status_code, res.text)
if res.status_code != 200: exit(1)
project_id = res.json()["id"]

# 2. Upload page
import cv2, numpy as np
img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
cv2.rectangle(img, (100, 100), (900, 900), (0, 0, 0), 2)
cv2.imwrite("dummy.png", img)

with open("dummy.png", "rb") as f:
    res = client.post(f"{API_BASE}/projects/{project_id}/pages", files={"file": ("dummy.png", f, "image/png")})
print("Upload page:", res.status_code, res.text)
if res.status_code != 200: exit(1)
page_id = res.json()["page_id"]

# 3. Preprocess
res = client.post(f"{API_BASE}/projects/{project_id}/pages/{page_id}/preprocess")
print("Preprocess:", res.status_code, res.text)
if res.status_code != 200: exit(1)

# 4. Detect diagrams
res = client.post(f"{API_BASE}/projects/{project_id}/pages/{page_id}/detect")
print("Detect:", res.status_code, res.text)
