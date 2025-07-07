# 💬 AI Self-Service Login Assistant

This is a proof-of-concept AI chatbot designed to help students resolve common login issues such as password problems, account lockouts, and MFA setup issues — without needing to contact the IT service desk.

Built with:
- 🐍 Python
- 🖼️ Streamlit (chat interface)
- 🧠 OpenRouter (LLM API)
- 📄 Mock user database (`users.json`)

---

## 🚀 Features

✅ Natural conversation flow (one step at a time)  
✅ Verifies student identity securely  
✅ Handles forgotten passwords and unlocks accounts  
✅ Sends temporary passwords via SMS (mocked)  
✅ Easy to adapt to real identity stores (e.g. Active Directory)

---

## 🛠️ How It Works

1. The user starts a chat and explains their issue.
2. If it's a login-related issue, the assistant asks for their student ID.
3. If identity is verified using `users.json`, the assistant:
   - Unlocks the account OR
   - Resets the password and sends it to the provided phone number.

---

## 📁 Project Structure

```bash
ai-selfservice-tool/
│
├── app.py              # Main Streamlit chatbot interface
├── users.json          # Mock database of student records
├── requirements.txt    # Python dependencies
├── .env                # Contains OpenRouter API key
└── README.md           # You're here!
```

## 🔐 Environment Variables

### Create a .env file in the root folder with:

```bash
OPENROUTER_API_KEY=your_api_key_here
```

## 📦 Installation

### Clone the repo:
```bash
git clone https://github.com/EidAbokor1/ai-selfservice-tool.git
cd ai-selfservice-tool
```

### Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Run the app:
```bash
streamlit run app.py
```

## 🧪 Testing

Try using one of these student IDs:

- `u12345` (Alex Smith)  
- `u67890` (Sara Khan)

The bot will guide you through identity verification and either unlock your account or reset your password.