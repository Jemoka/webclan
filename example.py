import requests

BASE_URL = "http://localhost:8889"

# Upload file
with open("/Users/houjun/Downloads/unix-clan/examples/progs/chip.cha", "rb") as f:
    response = requests.post(f"{BASE_URL}/upload", files={"file": f})
uid = response.json()["unique_id"]

# Execute command
response = requests.post(f"{BASE_URL}/execute", json={
    "unique_id": uid,
    "binary": "freq",
    "args": ["chip.cha"]
})
print(response.json()["stdout"])

# List files
response = requests.get(f"{BASE_URL}/list/{uid}")
print(response.json()["files"])

# Download file
response = requests.get(f"{BASE_URL}/download/{uid}/example.cha")
print(response.json()["content"])

# Cleanup
requests.delete(f"{BASE_URL}/cleanup/{uid}")
