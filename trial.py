import httpx

import os, certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

API_KEY = "AIzaSyALn5gEk1DeBNoIFRBdk52K3d_S5JKyC3M"  # or hardcode for test
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

headers = {
    "Content-Type": "application/json",
}

json_data = {
    "contents": [
        {
            "parts": [{"text": "Hello Gemini!"}]
        }
    ]
}

response = httpx.post(url, headers=headers, json=json_data)
print(response.status_code)
print(response.text)
