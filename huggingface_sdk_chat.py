"""
HuggingFace Chat using Official SDK - Zscaler SSL Bypass
Uses the official 'huggingface_hub' library with custom SSL context
"""

import os
import ssl
import httpx
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
CA_BUNDLE = os.getenv("CA_BUNDLE")


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


# Monkey-patch httpx to use our SSL context globally
# This is needed because InferenceClient doesn't accept custom http_client
_original_client_init = httpx.Client.__init__

def _patched_client_init(self, *args, **kwargs):
    if 'verify' not in kwargs or kwargs['verify'] is True:
        kwargs['verify'] = create_ssl_context()
    _original_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_client_init


def create_hf_client():
    """Create HuggingFace InferenceClient."""
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN not found in .env file")
    
    client = InferenceClient(
        api_key=HF_TOKEN,
    )
    
    return client


def query_huggingface(client, message, model="Qwen/Qwen2.5-7B-Instruct"):
    """Query HuggingFace using the official SDK."""
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": message}
        ],
        temperature=0.7,
        max_tokens=1024,
        top_p=0.9,
    )
    
    return response.choices[0].message.content


if __name__ == "__main__":
    print("=" * 50)
    print("HuggingFace Chat - Official SDK (Qwen/Qwen2.5-7B-Instruct)")
    print("Type 'exit' or 'quit' to stop")
    print("=" * 50)
    
    try:
        client = create_hf_client()
        print("✅ HuggingFace client initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        exit(1)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        try:
            answer = query_huggingface(client, user_input)
            print("\nAI:", answer)
        except Exception as e:
            print(f"\nError: {e}")
