import os, requests
from dotenv import load_dotenv
load_dotenv()
resp = requests.post("https://api.mistral.ai/v1/chat/completions", headers={"Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}", "Content-Type": "application/json"}, json={"model": "mistral-small-latest", "messages": [{"role": "user", "content": "hi"}]})
print(resp.headers)
