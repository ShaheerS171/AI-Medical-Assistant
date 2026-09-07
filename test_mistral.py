import os
import requests
from dotenv import load_dotenv
load_dotenv()
MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
key = os.getenv("MISTRAL_API_KEY")
print("Key exists:", bool(key))
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
payload = {
    "model": "mistral-small-latest",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 10
}
resp = requests.post(MISTRAL_CHAT_URL, headers=headers, json=payload)
print(resp.status_code)
print(resp.json())
