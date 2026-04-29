# Querra – University IT Self-Service

AI chatbot that helps students with password resets, account unlocks, and MFA issues — no IT ticket needed.

Built with Python, Streamlit, and OpenRouter (DeepSeek).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your API key to `.env`:

```
OPENROUTER_API_KEY=your_key_here
```

## Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Test Accounts

| ID | Name | Status |
|---|---|---|
| u12345 | Alex Smith | Active |
| u67890 | Sara Khan | Locked |

## How It Works

1. Student says what they need
2. Querra asks for their student ID
3. Identity is verified (name, postcode, DOB, phone)
4. Action is performed automatically

## GDPR

- Consent screen shown before chat starts
- PII is stripped from data sent to the AI
- All actions are logged to `audit.log`
