"""
Groq Chat using Official SDK - Zscaler SSL Bypass
Uses the official 'groq' library with custom SSL context
"""

import os
import ssl
import httpx
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
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


def create_groq_client():
    """Create Groq client with Zscaler SSL bypass."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in .env file")
    
    # Create custom httpx client with SSL context
    ssl_context = create_ssl_context()
    custom_http_client = httpx.Client(verify=ssl_context)
    
    # Pass custom client to Groq SDK
    client = Groq(
        api_key=GROQ_API_KEY,
        http_client=custom_http_client,
    )
    
    return client


def query_groq(client, message, model="llama-3.3-70b-versatile"):
    """Query Groq using the official SDK."""
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": message}
        ],
        model=model,
        temperature=0.7,
        max_tokens=1024,
        top_p=0.9,
    )
    
    return response.choices[0].message.content


if __name__ == "__main__":
    print("=" * 50)
    print("Groq Chat - Official SDK (llama-3.3-70b-versatile)")
    print("Type 'exit' or 'quit' to stop")
    print("=" * 50)
    
    try:
        client = create_groq_client()
        print("✅ Groq client initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        exit(1)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        try:
            answer = query_groq(client, user_input)
            print("\nAI:", answer)
        except Exception as e:
            print(f"\nError: {e}")
