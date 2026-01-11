import streamlit as st
import json
import os
import requests
import random
from dotenv import load_dotenv
from typing import Dict, Any
from datetime import datetime

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

def save_user_data(data: Dict[str, Any]):
    """Save updated user data back to JSON"""
    with open("users.json", "w") as f:
        json.dump(data, f, indent=2)

def reload_user_data():
    """Reload user data from file"""
    global USER_DATA
    USER_DATA = load_user_data()

USER_DATA = load_user_data()

# =====================
# AUDIT LOGGING
# =====================
def audit_log(action: str, user_id: str, status: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("audit.log", "a") as f:
        f.write(f"{timestamp} | {action} | {user_id} | {status}\n")

def get_audit_logs():
    """Read and parse audit log file"""
    try:
        with open("audit.log", "r") as f:
            return f.readlines()
    except FileNotFoundError:
        return []

# =====================
# MOCK EMAIL SYSTEM
# =====================
def send_mock_email(to: str, subject: str, body: str):
    """Simulate sending an email by storing it in session state"""
    if "inbox" not in st.session_state:
        st.session_state.inbox = []
    
    st.session_state.inbox.append({
        "to": to,
        "subject": subject,
        "body": body,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# =====================
# VERIFICATION LOGIC
# =====================
def verify_field(user_id: str, field: str, value: str) -> bool:
    record = USER_DATA.get(user_id)
    if not record:
        return False
    return record.get(field, "").lower() == value.lower()

# =====================
# SIMULATED ACTIONS (WITH REAL STATE CHANGES)
# =====================
def submit_password_reset(user_id: str):
    """Reset password and auto-unlock if needed"""
    # Reload data to get latest state
    reload_user_data()
    
    # Generate temporary password
    temp_password = f"Temp{random.randint(1000, 9999)}!"
    
    # Check if account is locked
    was_locked = USER_DATA[user_id].get("account_locked", False)
    
    # Unlock account first if locked (so they can access email)
    if was_locked:
        USER_DATA[user_id]["account_locked"] = False
    
    # Update password
    USER_DATA[user_id]["password"] = temp_password
    save_user_data(USER_DATA)
    
    # Send mock email with password
    user_email = USER_DATA[user_id].get("email", f"{user_id}@university.ac.uk")
    send_mock_email(
        to=user_email,
        subject="🔑 Password Reset Successful - Querra",
        body=f"""Hi {USER_DATA[user_id]['full_name']},

Your password has been reset successfully.

Temporary Password: {temp_password}

Please log in and change your password immediately.

- Querra IT Support"""
    )
    
    audit_log("PASSWORD_RESET", user_id, f"COMPLETED:{temp_password}")
    
    # Build response
    response = "✅ **Password reset successful!**\n\n"
    
    if was_locked:
        response += "🔓 Your account has been unlocked so you can access your email.\n\n"
    
    response += f"📧 A temporary password has been sent to **{user_email}**\n\n"
    response += "Please check the Mock Inbox to retrieve your password."
    
    return response

def submit_account_unlock(user_id: str):
    """Unlock account only - no email needed"""
    # Reload data to get latest state
    reload_user_data()
    
    # Unlock account
    USER_DATA[user_id]["account_locked"] = False
    save_user_data(USER_DATA)
    
    audit_log("ACCOUNT_UNLOCK", user_id, "COMPLETED")
    
    return f"""✅ **Account unlocked successfully!**

Your account is now active. You can log in immediately.

🔓 Status: **Active**
👤 Student ID: **{user_id}**

Try logging in now using the Test Login page!"""

def submit_mfa_reset(user_id: str):
    """Reset MFA in the mock database"""
    # Reload data to get latest state
    reload_user_data()
    
    # Reset MFA
    USER_DATA[user_id]["mfa_enabled"] = False
    save_user_data(USER_DATA)
    
    # Send mock email
    user_email = USER_DATA[user_id].get("email", f"{user_id}@university.ac.uk")
    send_mock_email(
        to=user_email,
        subject="📱 MFA Reset - Querra",
        body=f"""Hi {USER_DATA[user_id]['full_name']},

Your Multi-Factor Authentication has been reset.

You will be prompted to set up MFA again on your next login.

- Querra IT Support"""
    )
    
    audit_log("MFA_RESET", user_id, "COMPLETED")
    
    return f"""✅ **MFA reset successful!**

Your Multi-Factor Authentication has been removed.

📱 Next Steps:
- Log in to your account
- You'll be prompted to set up MFA again
- Follow the on-screen instructions

📧 Confirmation sent to **{user_email}**"""

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

CRITICAL RULES:
- You are ONLY responsible for conversation and gathering information
- You do NOT perform any actions (resets, unlocks, etc.)
- NEVER say "I've submitted" or "I've processed" or "request sent"
- The SYSTEM handles all actions after identity verification
- Ask one question at a time
- Be friendly, professional, and concise
- Redirect non-login issues to IT support

After identity verification, simply ask the user what they need help with. Do not confirm actions.
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    try:
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
            return "⚠️ I'm having trouble right now. Please try again."

        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return "⚠️ I'm having trouble connecting. Please try again."

# =====================
# TEST LOGIN PAGE
# =====================
def show_test_login():
    st.title("🔐 Mock University Login Portal")
    st.caption("Test the password resets and account unlocks here")
    
    st.info("💡 **Tip**: Try logging in with wrong credentials, then use Querra to fix it!")
    
    # Reload user data to show latest changes
    reload_user_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.text_input("Student ID", placeholder="e.g., u12345")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("🔑 Login", use_container_width=True):
            # Reload again right before login check
            reload_user_data()
            user = USER_DATA.get(user_id)
            
            if not user:
                st.error("❌ Invalid student ID")
            elif user.get("account_locked", False):
                st.error("🔒 **Account is locked**\n\nUse Querra to unlock your account.")
            elif user.get("password") != password:
                st.error("❌ **Incorrect password**\n\nUse Querra to reset your password.")
            else:
                st.success(f"✅ **Welcome back, {user['full_name']}!**")
                st.balloons()
    
    with col2:
        st.markdown("### 👥 Test Accounts")
        for uid, data in USER_DATA.items():
            status = "🔒 Locked" if data.get("account_locked", False) else "🔓 Active"
            st.code(f"ID: {uid}\nName: {data['full_name']}\nStatus: {status}\nPassword: {data.get('password', 'Not set')}", language=None)

# =====================
# DASHBOARD PAGE
# =====================
def show_dashboard():
    st.title("📊 Querra Analytics Dashboard")
    st.caption("Real-time insights into IT support automation")
    
    logs = get_audit_logs()
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Requests Handled", len(logs))
    
    with col2:
        st.metric("Estimated Tickets Avoided", len(logs))
    
    with col3:
        st.metric("Estimated Time Saved", f"{len(logs) * 5} min")
    
    st.divider()
    
    # Request breakdown
    if logs:
        password_resets = sum(1 for log in logs if "PASSWORD_RESET" in log)
        account_unlocks = sum(1 for log in logs if "ACCOUNT_UNLOCK" in log)
        mfa_resets = sum(1 for log in logs if "MFA_RESET" in log)
        resolved = sum(1 for log in logs if "RESOLVED" in log)
        escalated = sum(1 for log in logs if "ESCALATED" in log)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Request Types")
            st.write(f"🔑 Password Resets: **{password_resets}**")
            st.write(f"🔓 Account Unlocks: **{account_unlocks}**")
            st.write(f"📱 MFA Resets: **{mfa_resets}**")
        
        with col2:
            st.subheader("✅ Resolution Status")
            st.write(f"✅ Self-Resolved: **{resolved}**")
            st.write(f"🎫 Escalated to IT: **{escalated}**")
            if resolved + escalated > 0:
                success_rate = (resolved / (resolved + escalated)) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
    
    st.divider()
    
    # Recent activity
    st.subheader("📋 Recent Activity")
    
    if logs:
        for log in reversed(logs[-15:]):
            st.text(log.strip())
    else:
        st.info("No activity yet. Start using Querra to see analytics!")
    
    st.divider()
    
    # Export option
    if st.button("📥 Export Full Audit Log"):
        st.download_button(
            label="Download audit.log",
            data="".join(logs),
            file_name="querra_audit.log",
            mime="text/plain"
        )
    
    st.divider()
    
    # Demo Reset Controls
    st.subheader("⚠️ Demo Controls")
    st.caption("Use these buttons to reset the demo environment")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear Audit Log", use_container_width=True):
            with open("audit.log", "w") as f:
                f.write("")
            st.success("✅ Audit log cleared!")
            st.rerun()
    
    with col2:
        if st.button("📧 Clear Inbox", use_container_width=True):
            st.session_state.inbox = []
            st.success("✅ Inbox cleared!")
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset All Users", use_container_width=True):
            # Reset to original state
            reset_data = {
                "u12345": {
                    "full_name": "Alex Smith",
                    "dob": "2016-04-22",
                    "postcode": "SW1A 1AA",
                    "phone": "07700900123",
                    "email": "alex.smith@university.ac.uk",
                    "password": "Welcome123!",
                    "account_locked": False,
                    "mfa_enabled": True
                },
                "u67890": {
                    "full_name": "Sara Khan",
                    "dob": "2002-09-15",
                    "postcode": "E1 6AN",
                    "phone": "07700900234",
                    "email": "sara.khan@university.ac.uk",
                    "password": "Student456!",
                    "account_locked": True,
                    "mfa_enabled": True
                }
            }
            save_user_data(reset_data)
            st.success("✅ Users reset to defaults!")
            st.rerun()

# =====================
# STREAMLIT UI
# =====================
st.set_page_config(
    page_title="Querra – University IT Support",
    page_icon="🎓",
    layout="wide"
)

# =====================
# SIDEBAR
# =====================
with st.sidebar:
    st.markdown("# 🎓 Querra")
    st.caption("Kill the Queue. Querra IT.")
    
    st.divider()
    
    # Page selector
    page = st.radio("📍 Navigate", ["💬 Chat Support", "🔐 Test Login", "📊 Dashboard", "📧 Mock Inbox"], label_visibility="collapsed")
    
    st.divider()
    
    st.markdown("### 🔐 We can help with:")
    st.markdown("- 🔑 Password resets")
    st.markdown("- 🔓 Account unlocks")
    st.markdown("- 📱 MFA issues")
    
    st.divider()
    
    st.caption("**Need other help?**")
    st.caption("📧 support@university.ac.uk")
    st.caption("📞 +44 20 1234 5678")
    
    st.divider()
    
    if page == "💬 Chat Support":
        if st.button("🔄 Clear Chat", use_container_width=True):
            keys_to_delete = ["stage", "user_id", "verify_step", "history", "messages"]
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# =====================
# PAGE ROUTING
# =====================
if page == "📊 Dashboard":
    show_dashboard()
    st.stop()

if page == "🔐 Test Login":
    show_test_login()
    st.stop()

if page == "📧 Mock Inbox":
    st.title("📧 Mock Email Inbox")
    st.caption("All simulated emails sent by Querra appear here")
    
    # Clear Inbox button at the top
    if st.button("🗑️ Clear All Emails", use_container_width=False):
        st.session_state.inbox = []
        st.success("✅ Inbox cleared!")
        st.rerun()
    
    st.divider()
    
    if "inbox" in st.session_state and st.session_state.inbox:
        st.info(f"📬 You have **{len(st.session_state.inbox)}** email(s)")
        for i, email in enumerate(reversed(st.session_state.inbox)):
            with st.expander(f"📨 {email['subject']} - {email['timestamp']}"):
                st.markdown(f"**To:** {email['to']}")
                st.markdown(f"**Subject:** {email['subject']}")
                st.divider()
                st.text(email['body'])
    else:
        st.info("📭 No emails yet. Use Querra to reset a password or unlock an account!")
    
    st.stop()

# =====================
# CHAT PAGE
# =====================
st.title("💬 Chat with Querra")
st.caption("Your AI IT assistant – here to help you get back to learning")

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "greeting"
    st.session_state.user_id = ""
    st.session_state.verify_step = "full_name"
    st.session_state.history = []
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I'm **Querra**, your AI IT assistant.\n\n"
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
            ai_reply = "Thanks. Let's verify your identity. What is your **full name**?"
            st.session_state.stage = "verifying"
            st.session_state.verify_step = "full_name"
        else:
            ai_reply = "I couldn't find that ID. Please try again."

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
            ai_reply = "❌ That doesn't match our records. Please contact IT support."
            audit_log("VERIFICATION_FAILED", st.session_state.user_id or "UNKNOWN", "FAILED")
            st.session_state.stage = "done"

    elif stage == "action":
        user_id = st.session_state.user_id
        text = user_input.lower()

        # Execute the action directly based on keywords
        if "password" in text or "reset" in text:
            ai_reply = submit_password_reset(user_id)
            ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
            st.session_state.stage = "feedback"
        elif "unlock" in text or "locked" in text:
            ai_reply = submit_account_unlock(user_id)
            ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
            st.session_state.stage = "feedback"
        elif "mfa" in text or "authenticat" in text:
            ai_reply = submit_mfa_reset(user_id)
            ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
            st.session_state.stage = "feedback"
        else:
            # If unclear, ask AI to clarify
            ai_reply = get_ai_response(user_input, st.session_state.history)
            # Don't change stage - stay in action to wait for clear choice

    elif stage == "feedback":
        user_id = st.session_state.user_id
        if "yes" in user_input.lower():
            ai_reply = "🎉 Great! Have a wonderful day, and happy studying!"
            audit_log("FEEDBACK", user_id, "RESOLVED")
        else:
            ticket_ref = f"QR-{user_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
            ai_reply = f"I'll create a ticket for our IT team.\n\n📋 Reference: **{ticket_ref}**\n\nThey'll be in touch soon!"
            audit_log("FEEDBACK", user_id, "ESCALATED")
        st.session_state.stage = "done"

    else:
        ai_reply = get_ai_response(user_input, st.session_state.history)

    # Save history
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": ai_reply})
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    with st.chat_message("assistant"):
        st.markdown(ai_reply)