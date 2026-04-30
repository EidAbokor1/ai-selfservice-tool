# Querra – AI IT Self-Service for Education

> Kill the queue. Querra IT.

Querra is an AI-powered IT support chatbot built for universities, colleges, and schools. It handles the high-volume, low-complexity tickets that clog up helpdesks — password resets, account lockouts, and MFA issues — so your IT team can focus on what matters.

## The Problem

IT helpdesks in education are overwhelmed by repetitive login issues, especially during enrolment and start of term. Each ticket costs £5–15 in staff time, and students wait hours or days for a 2-minute fix.

## The Solution

Querra verifies student identity through security questions, then resolves the issue automatically — no human needed.

**Supported actions:**
- 🔑 Password resets (generates temp password, notifies student)
- 🔓 Account unlocks
- 📱 MFA resets

**Built-in compliance:**
- GDPR consent gate before data collection
- PII stripped from all AI processing
- Full audit trail of every action
- Rate-limited verification (account freezes after 3 failed attempts)

## Demo

```bash
# Clone and run locally
git clone https://github.com/EidAbokor1/ai-selfservice-tool.git
cd ai-selfservice-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add your OpenRouter API key
echo "OPENROUTER_API_KEY=your_key" > .env

# Launch
streamlit run app.py
```

Test accounts: `u12345` (Alex Smith, active) and `u67890` (Sara Khan, locked).

## How It Works

1. Student describes their issue in plain language
2. Querra asks which system they're trying to access
3. Identity is verified with randomised security questions
4. Action is performed automatically and logged

## Roadmap

- [ ] Active Directory / Azure AD integration
- [ ] Admin dashboard with ticket deflection metrics
- [ ] UK/EU-hosted LLM for full GDPR compliance
- [ ] Multi-tenancy for SaaS deployment
- [ ] Microsoft Teams / Slack integration

## Contact

Interested in piloting Querra at your institution? Get in touch.
