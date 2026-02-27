"""
HuggingFace Chat - Zscaler SSL Bypass
Uses HuggingFace Inference API with Qwen model
"""

import os
import ssl
import httpx
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
CA_BUNDLE = os.getenv("CA_BUNDLE")

API_URL = "https://router.huggingface.co/v1/chat/completions"


def create_ssl_context():
    """Create SSL context with relaxed verification for Zscaler."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    # Disable strict X.509 check for Zscaler compatibility
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    if CA_BUNDLE and os.path.isfile(CA_BUNDLE):
        ctx.load_verify_locations(CA_BUNDLE)
    return ctx


def query_huggingface(message, model="Qwen/Qwen2.5-7B-Instruct"):
    """Query HuggingFace Inference API."""
    
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN not found in .env file")
    
    ssl_context = create_ssl_context()
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
        "top_p": 0.9,
        "stream": False
    }

    with httpx.Client(verify=ssl_context) as client:
        response = client.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print("=" * 50)
    print("HuggingFace Chat (Qwen/Qwen2.5-7B-Instruct)")
    print("Type 'exit' or 'quit' to stop")
    print("=" * 50)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        try:
            answer = query_huggingface(user_input)
            print("\nAI:", answer)
        except Exception as e:
            print(f"\nError: {e}")
