import os
import ssl
import json
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

load_dotenv()

CA_BUNDLE = os.getenv("CA_BUNDLE")
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

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

# Change model-id as required
# Different models have different request format - check proper format
# Below format is for model-id `arcee-ai/trinity-large-preview:free`
# First API call with reasoning
# API call should be done with this session obejct
response = session.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "arcee-ai/trinity-large-preview:free",
    "messages": [
        {
          "role": "user",
          "content": "How many r's are in the word 'strawberry'?"
        }
      ],
    "reasoning": {"enabled": True}
  })
)

# Extract the response
result = response.json()

# Print reasoning if available
reasoning = result["choices"][0]["message"].get("reasoning_content")
if reasoning:
    print(f"\nReasoning: {reasoning}")

# Print the actual answer
answer = result["choices"][0]["message"]["content"]
print(f"\nResponse: {answer}")

