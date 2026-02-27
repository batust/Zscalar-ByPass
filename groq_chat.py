"""
Groq Chat - Zscaler SSL Bypass
Simple direct API implementation (no Agno needed)
"""

import os
import ssl
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CA_BUNDLE = os.getenv("CA_BUNDLE")

API_URL = "https://api.groq.com/openai/v1/chat/completions"


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


def query_groq(message, model="llama-3.3-70b-versatile"):
    """Query Groq API with Zscaler SSL bypass."""
    
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in .env file")
    
    ssl_context = create_ssl_context()
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_completion_tokens": 1024,  
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
    print("Groq Chat (llama-3.3-70b-versatile)")
    print("Type 'exit' or 'quit' to stop")
    print("=" * 50)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        try:
            answer = query_groq(user_input)
            print("\nAI:", answer)
        except Exception as e:
            print(f"\nError: {e}")
