import streamlit as st
import json
import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any

# =====================
# CONFIG
# =====================
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
SIMULATION_MODE = True  # IMPORTANT for MVP demos

# =====================
# DATA LOADING
# =====================
def load_user_data() -> Dict[str, Any]:
    try:
        with open("users.json") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("users.json not found")
        st.stop()

USER_DATA = load_user_data()

# =====================
# AUDIT LOGGING
# =====================
def audit_log(action: str, user_id: str, status: str):
    with open("audit.log", "a") as f:
        f.write(f"{action} | {user_id} | {status}\n")

# =====================
# VERIFICATION LOGIC
# =====================
def verify_field(user_id: str, field: str, value: str) -> bool:
    record = USER_DATA.get(user_id)
    if not record:
        return False
    return record.get(field, "").lower() == value.lower()

# =====================
# SIMULATED ACTIONS
# =====================
def submit_password_reset(user_id: str):
    audit_log("PASSWORD_RESET", user_id, "REQUESTED")
    return "✅ A secure password reset request has been submitted. You’ll receive official instructions shortly."

def submit_account_unlock(user_id: str):
    audit_log("ACCOUNT_UNLOCK", user_id, "REQUESTED")
    return "✅ Your account unlock request has been submitted. Please try again in a few minutes."

def submit_mfa_reset(user_id: str):
    audit_log("MFA_RESET", user_id, "REQUESTED")
    return "✅ Your MFA reset request has been submitted. You’ll be asked to re-register MFA on your next login."

# =====================
# AI (LANGUAGE ONLY)
# =====================
def get_ai_response(user_input: str, history: list) -> str:
    system_prompt = """
You are Querra, an AI IT support assistant for a university.

You can ONLY assist with:
- Password reset requests
- Account unlock requests
- MFA reset requests

RULES:
- Never generate or share passwords
- Never claim actions were completed
- Ask one question at a time
- Be friendly, professional, and concise
- Redirect non-login issues to IT support

You ONLY assist with conversation.
All actions are handled by the system.
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek/deepseek-chat-v3",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 300
        },
        timeout=15
    )

    if response.status_code != 200:
        return "⚠️ I’m having trouble right now. Please try again."

    return response.json()["choices"][0]["message"]["content"]

# =====================
# STREAMLIT UI
# =====================
st.set_page_config(page_title="Querra – Kill the Queue", page_icon="💬")
st.title("💬 Querra")
st.caption("Kill the queue. Querra it.")

if "stage" not in st.session_state:
    st.session_state.stage = "greeting"
    st.session_state.user_id = ""
    st.session_state.verify_step = "full_name"
    st.session_state.history = []
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I’m **Querra**, your AI IT assistant.\n\n"
                "I can help with:\n"
                "• Password resets\n"
                "• Locked accounts\n"
                "• MFA issues\n\n"
                "How can I help today?"
            )
        }
    ]

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =====================
# CHAT INPUT
# =====================
if user_input := st.chat_input("Message Querra…"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # ---- STAGE HANDLING ----
    stage = st.session_state.stage

    if stage == "greeting":
        ai_reply = get_ai_response(user_input, st.session_state.history)
        st.session_state.stage = "awaiting_issue"

    elif stage == "awaiting_issue":
        ai_reply = get_ai_response(user_input, st.session_state.history)
        if "student id" in ai_reply.lower():
            st.session_state.stage = "awaiting_user_id"

    elif stage == "awaiting_user_id":
        if user_input in USER_DATA:
            st.session_state.user_id = user_input
            ai_reply = "Thanks. Let’s verify your identity. What is your **full name**?"
            st.session_state.stage = "verifying"
            st.session_state.verify_step = "full_name"
        else:
            ai_reply = "I couldn’t find that ID. Please try again."

    elif stage == "verifying":
        user_id = st.session_state.user_id
        step = st.session_state.verify_step

        if verify_field(user_id, step, user_input):
            if step == "full_name":
                st.session_state.verify_step = "postcode"
                ai_reply = "Thanks. What is your **postcode**?"
            elif step == "postcode":
                st.session_state.verify_step = "dob"
                ai_reply = "Great. What is your **date of birth**? (YYYY-MM-DD)"
            elif step == "dob":
                st.session_state.verify_step = "phone"
                ai_reply = "Almost done. What is your **phone number**?"
            elif step == "phone":
                ai_reply = (
                    "✅ Identity verified.\n\n"
                    "What would you like to do?\n"
                    "• Reset password\n"
                    "• Unlock account\n"
                    "• Reset MFA"
                )
                st.session_state.stage = "action"
        else:
            ai_reply = "❌ That doesn’t match our records. Please contact IT support."
            st.session_state.stage = "done"

    elif stage == "action":
        user_id = st.session_state.user_id
        text = user_input.lower()

        if "password" in text:
            ai_reply = submit_password_reset(user_id)
        elif "unlock" in text:
            ai_reply = submit_account_unlock(user_id)
        elif "mfa" in text:
            ai_reply = submit_mfa_reset(user_id)
        else:
            ai_reply = "Please choose one of the available options."

        st.session_state.stage = "done"

    else:
        ai_reply = get_ai_response(user_input, st.session_state.history)

    # Save history
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": ai_reply})
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    with st.chat_message("assistant"):
        st.markdown(ai_reply)

