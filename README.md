## Using HuggingFace, OpenRouter, Groq APIs in corporate laps by bypassing Zscalar
## Test this with other model ids from HuggingFace too


A simple command-line chatbot that talks to **Qwen/Qwen2.5-7B-Instruct** via the [HuggingFace Inference Providers API](https://huggingface.co/docs/inference-providers/index), with built-in support for **Zscaler SSL inspection** on corporate networks.

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Python** | 3.10 or higher |
| **HuggingFace Token** | Free account → [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| **Zscaler Root CA** | Required if you are on a corporate network with SSL inspection (see below) |

---

## 1 — Export the Zscaler Root CA Certificate

If your organisation uses **Zscaler** (or any other SSL-inspecting proxy), you need to export the root CA certificate so Python can verify HTTPS connections.

### Steps (Chrome / Edge)

1. Open **[https://google.com](https://google.com)** in your browser.
2. Click the **🔒 Padlock** icon in the address bar.
3. Click **"Connection is secure"**.
4. Click **"Certificate"** (or "Certificate is valid").
5. In the Certificate viewer, go to the **Details** tab.
6. In the certificate hierarchy at the top, select **"Zscaler Root CA"** (the topmost entry).
7. Click **"Export…"** and save the file to a local folder, for example:
   ```
   C:\Users\<YourUser>\Downloads\Work Folder\TESTER\Zscaler Root CA.crt
   ```
   > Make sure you save it as **Base-64 encoded X.509 (.CER / .CRT)**.

---

## 2 — Set SSL Environment Variables (PowerShell)

After exporting the certificate, open **PowerShell** and set the following environment variables so that Python libraries (requests, urllib3, boto3, etc.) trust the Zscaler certificate.

> **Replace** `"C:\path\to\your\Zscaler Root CA.crt"` with the actual path to the `.crt` file you saved in Step 1. You can **right-click → Copy as path** on the file in File Explorer.

```powershell
# Tell Python 'requests' / urllib3 to use the Zscaler cert
$env:REQUESTS_CA_BUNDLE = "C:\path\to\your\Zscaler Root CA.crt"
$env:SSL_CERT_FILE      = "C:\path\to\your\Zscaler Root CA.crt"

# Tell AWS SDK (boto3) to use the Zscaler cert
$env:AWS_CA_BUNDLE = "C:\path\to\your\Zscaler Root CA.crt"
```

> ⚠️ These variables are **session-scoped** — they last only for the current PowerShell window. To make them permanent, add them to your [User Environment Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables) or your PowerShell `$PROFILE`.

---

## 3 — Setup

```powershell
# Clone / navigate to the project folder
cd "C:\Users\<YourUser>\Downloads\Work Folder\TESTER"

# Create and activate a virtual environment
python -m venv myenv
.\myenv\Scripts\Activate.ps1

# Install dependencies
pip install requests python-dotenv
```

---

## 4 — Configure .env

Copy the example and fill in your values:

```powershell
copy .env.example .env
```

Then open `.env` and set:

| Variable | Description |
|---|---|
| `HF_TOKEN` | Your HuggingFace API token (starts with `hf_`) |
| `CA_BUNDLE` | Full path to the Zscaler Root CA `.crt` file you exported in Step 1 |

Example `.env`:

```properties
HF_TOKEN=hf_abcDEF123456789
CA_BUNDLE="C:\Users\YourUser\Downloads\Work Folder\TESTER\Zscaler Root CA.crt"
```

---

## 5 — Run

```powershell
python .\gooo.py
```

You should see:

```
You: Hello!

AI: Hi there! How can I help you today?
```

Type **`exit`** or **`quit`** to stop.

---

## How It Works

`gooo.py` calls the **HuggingFace Inference Providers** [OpenAI-compatible chat completions endpoint](https://huggingface.co/docs/inference-providers/index):

```
POST https://router.huggingface.co/v1/chat/completions
```

Because Python 3.13+ has stricter X.509 validation, the Zscaler Root CA (whose Basic Constraints extension is not marked "critical") would normally be rejected. The code uses a custom `requests` adapter (`ZscalerAdapter`) that:

1. Creates an SSL context with hostname checking **enabled**.
2. Disables **only** the `VERIFY_X509_STRICT` flag — the one rule that rejects the Zscaler cert.
3. Loads your Zscaler CA from the `CA_BUNDLE` path.

This keeps traffic **encrypted and verified** while working around the single strict check.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `python-dotenv could not parse statement` | Invalid syntax in `.env` (e.g. bare `===` lines) | Remove any lines that aren't `KEY=VALUE` or `# comments` |
| `CERTIFICATE_VERIFY_FAILED: Basic Constraints of CA cert not marked critical` | Python 3.13 strict X.509 check rejects Zscaler cert | Ensure `CA_BUNDLE` is set correctly in `.env` — the `ZscalerAdapter` handles the rest |
| `Error 404: Not Found` | Wrong API URL or model name | Make sure `API_URL` is `https://router.huggingface.co/v1/chat/completions` |
| `Error 400: model not found` | Model no longer available on Inference Providers | Change the `model` field in the payload to a currently available model (e.g. `Qwen/Qwen2.5-7B-Instruct`) |
| `InsecureRequestWarning` | `CA_BUNDLE` path is missing/wrong, falling back to `verify=False` | Double-check the path in `.env` points to a valid `.crt` file |

```
