import os
import ssl
import requests
from dotenv import load_dotenv
from urllib3.util.ssl_ import create_urllib3_context
from requests.adapters import HTTPAdapter

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
CA_BUNDLE = os.getenv("CA_BUNDLE")

API_URL = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}


class ZscalerAdapter(HTTPAdapter):
    """Custom adapter that loads the Zscaler CA cert with relaxed verification
    so that Python 3.13's stricter 'Basic Constraints must be critical' check
    does not reject the certificate."""

    def __init__(self, ca_cert_path, **kwargs):
        self.ca_cert_path = ca_cert_path
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        # VERIFY_X509_STRICT is what enforces the "critical" check — disable it
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        ctx.load_verify_locations(self.ca_cert_path)
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def _build_session():
    """Return a requests.Session wired up with the Zscaler CA bundle."""
    session = requests.Session()
    if CA_BUNDLE and os.path.isfile(CA_BUNDLE):
        adapter = ZscalerAdapter(CA_BUNDLE)
        session.mount("https://", adapter)
    else:
        # Fallback: disable verification entirely (not recommended)
        session.verify = False
    return session


session = _build_session()


def query_llm(message):

    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 200,
        "top_p": 0.9,
        "stream": False
    }

    response = session.post(
        API_URL,
        headers=headers,
        json=payload,
    )

    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        answer = query_llm(user_input)
        print("\nAI:", answer)
