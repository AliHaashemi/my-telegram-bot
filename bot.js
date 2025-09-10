import requests

API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b-it"
HF_TOKEN = "توکن_خود_را_اینجا_بگذارید"  # یا از متغیر محیطی بگیرید

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def query(prompt):
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    return response.json()

output = query("سلام، چطوری؟")
print(output)
