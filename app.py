import streamlit as st
import json
import os
import re
import string
import random
import requests
from dotenv import load_dotenv
from datetime import datetime

# =====================
# CONFIG
# =====================
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
AUDIT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit.log")

# =====================
# DATA
# =====================
def load_users():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =====================
# AUDIT LOGGING
# =====================
def audit_log(action: str, user_id: str, status: str):
    """Log actions for GDPR compliance and accountability."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(AUDIT_FILE, "a") as f:
        f.write(f"{timestamp} | {action} | {user_id} | {status}\n")

# =====================
# PII SANITISATION
# =====================
def sanitise_for_llm(history):
    """Strip PII from chat history before sending to external LLM.
    Replaces student IDs, names, postcodes, DOBs, phone numbers, and emails
    so no personal data leaves the system."""
    sanitised = []
    for msg in history:
        text = msg["content"]
        # Student IDs (u followed by digits)
        text = re.sub(r"\bu\d{4,}\b", "[STUDENT_ID]", text, flags=re.IGNORECASE)
        # UK postcodes
        text = re.sub(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", "[POSTCODE]", text, flags=re.IGNORECASE)
        # Dates (YYYY-MM-DD)
        text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "[DOB]", text)
        # UK phone numbers
        text = re.sub(r"\b0\d{10}\b", "[PHONE]", text)
        text = re.sub(r"\b07\d{9}\b", "[PHONE]", text)
        # Email addresses
        text = re.sub(r"\b[\w.-]+@[\w.-]+\.\w+\b", "[EMAIL]", text)
        sanitised.append({"role": msg["role"], "content": text})
    return sanitised

# =====================
# ACTIONS
# =====================
def generate_temp_password():
    """Generate a secure temporary password."""
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice("!@#$%&*")
    rest = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    password = list(upper + lower + digit + special + rest)
    random.shuffle(password)
    return ''.join(password)

def do_password_reset(user_id):
    users = load_users()
    user = users[user_id]
    temp_password = generate_temp_password()
    users[user_id]["password"] = temp_password
    save_users(users)
    audit_log("PASSWORD_RESET", user_id, "COMPLETED")
    return (
        "🔑 **Password Reset**\n\n"
        f"Your password has been reset. A temporary password has been sent to **{user['email']}**.\n\n"
        f"📧 *(For demo purposes, your temp password is: `{temp_password}`)*\n\n"
        "⚠️ Please change this password after your first login.\n\n"
        "Let me know if you need help with anything else!"
    )

def do_account_unlock(user_id):
    users = load_users()
    users[user_id]["account_locked"] = False
    save_users(users)
    audit_log("ACCOUNT_UNLOCK", user_id, "COMPLETED")
    return (
        "🔓 **Account Unlocked**\n\n"
        f"Your account (**{user_id}**) is now active. You can log in immediately.\n\n"
        "Let me know if you need help with anything else!"
    )

def do_mfa_reset(user_id):
    users = load_users()
    users[user_id]["mfa_enabled"] = False
    save_users(users)
    audit_log("MFA_RESET", user_id, "COMPLETED")
    return (
        "📱 **MFA Reset**\n\n"
        "Your multi-factor authentication has been removed.\n"
        "You'll be prompted to set it up again on your next login.\n\n"
        "Let me know if you need help with anything else!"
    )

# =====================
# AI RESPONSE
# =====================
def get_ai_response(user_input, history):
    system_prompt = """You are Querra, a friendly university IT support assistant.
You help with: password resets, account unlocks, and MFA resets.
Keep responses short and helpful. Ask for the student ID if needed.
Redirect non-login issues to support@university.ac.uk.
NEVER ask for or repeat any personal information like names, dates of birth, or phone numbers."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(sanitise_for_llm(history))
    messages.append({"role": "user", "content": user_input})

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek/deepseek-chat-v3", "messages": messages, "temperature": 0.3, "max_tokens": 200},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return "⚠️ I'm having trouble connecting. Please try again."

# =====================
# IDENTITY VERIFICATION
# =====================
VERIFY_STEPS = ["full_name", "postcode", "dob", "phone"]
VERIFY_PROMPTS = {
    "full_name": "What is your **full name**?",
    "postcode": "What is your **postcode**?",
    "dob": "What is your **date of birth**? (YYYY-MM-DD)",
    "phone": "What is your **phone number**?",
}

def verify_field(user_id, field, value):
    users = load_users()
    record = users.get(user_id)
    if not record:
        return False
    return record.get(field, "").lower() == value.strip().lower()

# =====================
# STREAMLIT UI
# =====================
st.set_page_config(page_title="Querra – IT Support", page_icon="🎓", layout="centered")

# =====================
# GDPR CONSENT GATE
# =====================
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False

if not st.session_state.consent_given:
    st.title("🎓 Querra – IT Self-Service")
    st.markdown("---")
    st.markdown("### Before we start")
    st.markdown(
        "To help resolve your IT issue, Querra will ask you to verify your identity "
        "using personal information (name, date of birth, postcode, phone number).\n\n"
        "**How we handle your data:**\n"
        "- Your personal details are checked locally and **not stored** beyond this session\n"
        "- Conversation is processed by an AI assistant to understand your request\n"
        "- Personal details are **stripped from AI conversations** before processing\n"
        "- An audit log records actions taken (e.g. account unlock) for security purposes\n"
        "- No data is shared with third parties beyond what is needed to operate this service\n\n"
        "For full details, see the [University Privacy Policy](https://university.ac.uk/privacy)."
    )
    st.markdown("")
    if st.button("✅ I understand and agree — start chat", use_container_width=True):
        st.session_state.consent_given = True
        audit_log("CONSENT", "ANONYMOUS", "GDPR_CONSENT_GIVEN")
        st.rerun()
    st.stop()

# =====================
# SIDEBAR
# =====================
with st.sidebar:
    st.markdown("# 🎓 Querra")
    st.caption("University IT Self-Service")
    st.divider()
    st.markdown("**I can help with:**")
    st.markdown("- 🔑 Password resets")
    st.markdown("- 🔓 Account unlocks")
    st.markdown("- 📱 MFA issues")
    st.divider()
    st.caption("Other issues → support@university.ac.uk")
    st.divider()
    if st.button("🔄 Clear Chat", use_container_width=True):
        consent = st.session_state.consent_given
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.consent_given = consent
        st.rerun()

st.title("💬 Chat with Querra")
st.caption("Your AI IT assistant")

# =====================
# SESSION STATE
# =====================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": (
            "👋 Hi! I'm **Querra**, your IT assistant.\n\n"
            "I can help with:\n"
            "• Password resets\n"
            "• Locked accounts\n"
            "• MFA issues\n\n"
            "What do you need help with?"
        )}
    ]
    st.session_state.history = []
    st.session_state.stage = "greeting"
    st.session_state.user_id = ""
    st.session_state.verify_index = 0

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =====================
# CHAT LOGIC
# =====================
if user_input := st.chat_input("Message Querra…"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    stage = st.session_state.stage
    text = user_input.lower().strip()
    reply = ""

    # --- GREETING / AWAITING ISSUE ---
    if stage in ("greeting", "awaiting_issue"):
        if any(w in text for w in ["password", "reset", "forgot"]):
            reply = "I can help with that. What's your **student ID**?"
            st.session_state.stage = "awaiting_id"
            st.session_state.pending_action = "password"
        elif any(w in text for w in ["unlock", "locked", "lock"]):
            reply = "I can help unlock your account. What's your **student ID**?"
            st.session_state.stage = "awaiting_id"
            st.session_state.pending_action = "unlock"
        elif any(w in text for w in ["mfa", "authenticat", "multi-factor", "2fa"]):
            reply = "I can help reset your MFA. What's your **student ID**?"
            st.session_state.stage = "awaiting_id"
            st.session_state.pending_action = "mfa"
        else:
            reply = get_ai_response(user_input, st.session_state.history)
            st.session_state.stage = "awaiting_issue"

    # --- AWAITING STUDENT ID ---
    elif stage == "awaiting_id":
        users = load_users()
        if user_input.strip() in users:
            st.session_state.user_id = user_input.strip()
            st.session_state.verify_index = 0
            step = VERIFY_STEPS[0]
            reply = f"Got it. Let's verify your identity.\n\n{VERIFY_PROMPTS[step]}"
            st.session_state.stage = "verifying"
            audit_log("VERIFICATION_START", st.session_state.user_id, "STARTED")
        else:
            reply = "I couldn't find that student ID. Please check and try again."

    # --- IDENTITY VERIFICATION ---
    elif stage == "verifying":
        idx = st.session_state.verify_index
        field = VERIFY_STEPS[idx]

        if verify_field(st.session_state.user_id, field, user_input):
            idx += 1
            st.session_state.verify_index = idx

            if idx < len(VERIFY_STEPS):
                next_field = VERIFY_STEPS[idx]
                reply = f"✅ Correct.\n\n{VERIFY_PROMPTS[next_field]}"
            else:
                # All verified — perform the action
                action = st.session_state.get("pending_action", "")
                uid = st.session_state.user_id
                audit_log("VERIFICATION_COMPLETE", uid, "VERIFIED")

                if action == "password":
                    reply = f"✅ Identity verified.\n\n{do_password_reset(uid)}"
                elif action == "unlock":
                    reply = f"✅ Identity verified.\n\n{do_account_unlock(uid)}"
                elif action == "mfa":
                    reply = f"✅ Identity verified.\n\n{do_mfa_reset(uid)}"
                else:
                    reply = (
                        "✅ Identity verified.\n\nWhat would you like to do?\n"
                        "• Reset password\n• Unlock account\n• Reset MFA"
                    )
                    st.session_state.stage = "choose_action"

                if action:
                    st.session_state.stage = "awaiting_issue"
        else:
            audit_log("VERIFICATION_FAILED", st.session_state.user_id, f"FAILED_ON:{field}")
            reply = "❌ That doesn't match our records. Please contact **support@university.ac.uk** for help."
            st.session_state.stage = "awaiting_issue"

    # --- CHOOSE ACTION (fallback if no action was pre-selected) ---
    elif stage == "choose_action":
        uid = st.session_state.user_id
        if any(w in text for w in ["password", "reset"]):
            reply = do_password_reset(uid)
        elif any(w in text for w in ["unlock", "locked"]):
            reply = do_account_unlock(uid)
        elif any(w in text for w in ["mfa", "authenticat"]):
            reply = do_mfa_reset(uid)
        else:
            reply = "Please choose one:\n• Reset password\n• Unlock account\n• Reset MFA"

        if reply != "Please choose one:\n• Reset password\n• Unlock account\n• Reset MFA":
            st.session_state.stage = "awaiting_issue"

    # --- FALLBACK ---
    else:
        reply = get_ai_response(user_input, st.session_state.history)
        st.session_state.stage = "awaiting_issue"

    # Save and display
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)
