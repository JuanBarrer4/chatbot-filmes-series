import requests
from dotenv import load_dotenv
import os

load_dotenv()

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user","content": "dame la respuesta de que es la vida"}
        ]
    }
)

data = response.json()
print(data["choices"][0]["message"]["content"])