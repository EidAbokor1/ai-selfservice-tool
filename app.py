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
def get_json_path():
    """Get the path to users.json file"""
    # Try multiple paths to find users.json
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json"),
        os.path.join(os.getcwd(), "users.json"),
        "users.json",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    # If none exist, try to create in the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "users.json")

def load_user_data() -> Dict[str, Any]:
    try:
        json_path = get_json_path()
        with open(json_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("users.json not found")
        st.stop()

def save_user_data(data: Dict[str, Any]):
    """Save updated user data back to JSON"""
    try:
        json_path = get_json_path()
        # Ensure directory exists if path has a directory component
        dir_path = os.path.dirname(json_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            f.flush()  # Ensure data is written immediately
        # Reload global data after save to keep it in sync
        reload_user_data()
    except Exception as e:
        st.error(f"Error saving user data: {str(e)}")
        raise

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
    """Guide user to self-service password reset portal"""
    # Reload data to get latest state
    reload_user_data()
    
    # Check if account is locked
    was_locked = USER_DATA[user_id].get("account_locked", False)
    
    user_email = USER_DATA[user_id].get("email", f"{user_id}@university.ac.uk")
    
    audit_log("PASSWORD_RESET_GUIDE", user_id, "GUIDED_TO_PORTAL")
    
    # Build response - comprehensive step-by-step guide
    response = "🔑 **Password Reset Process**\n\n"
    
    if was_locked:
        response += "✅ Good news - I've already unlocked your account so you can proceed with the password reset.\n\n"
    
    response += "Follow these steps to reset your password:\n\n"
    response += "**Step 1: Access the Password Reset Portal**\n"
    response += "🌐 Click this link: **https://selfservice.university.ac.uk/password-reset**\n"
    response += "   (Or copy and paste it into your browser)\n\n"
    
    response += "**Step 2: Enter Your Student ID**\n"
    response += "📝 Enter your student ID: **" + user_id + "**\n\n"
    
    response += "**Step 3: Verify Your Identity**\n"
    response += "🔐 You'll be asked to verify your identity. This may include:\n"
    response += "   • Your full name: **" + USER_DATA[user_id].get("full_name", "N/A") + "**\n"
    response += "   • Your date of birth\n"
    response += "   • Security questions (if you've set them up)\n\n"
    
    response += "**Step 4: Create Your New Password**\n"
    response += "🔒 **Password Requirements:**\n"
    response += "   • At least 8 characters long\n"
    response += "   • Must include at least one uppercase letter (A-Z)\n"
    response += "   • Must include at least one lowercase letter (a-z)\n"
    response += "   • Must include at least one number (0-9)\n"
    response += "   • Must include at least one special character (!@#$%^&*)\n"
    response += "   • Cannot be the same as your last 3 passwords\n\n"
    
    response += "**Step 5: Confirm and Save**\n"
    response += "✅ Enter your new password twice to confirm it matches\n"
    response += "✅ Click 'Save' or 'Reset Password' to complete the process\n\n"
    
    response += "**After resetting your password:**\n"
    response += "• You'll be able to log in with your new password immediately\n"
    response += "• You may be prompted to set up MFA again\n\n"
    
    response += "❓ **Need Help?**\n"
    response += "If you're unable to access the portal or complete any of these steps, let me know and I'll create a ticket for our IT support team to help you further."
    
    return response

def submit_account_unlock(user_id: str):
    """Unlock account only - no email needed"""
    try:
        # Reload data to get latest state
        reload_user_data()
        
        # Check if user exists
        if user_id not in USER_DATA:
            return f"❌ User ID {user_id} not found."
        
        # Check current state
        was_locked = USER_DATA[user_id].get("account_locked", False)
        
        # Unlock account
        USER_DATA[user_id]["account_locked"] = False
        
        # Save to file - this is critical!
        save_user_data(USER_DATA)  # This will also reload the data
        
        # Double-check the save worked by reading the file directly
        json_path = get_json_path()
        with open(json_path, "r") as f:
            saved_data = json.load(f)
        is_unlocked = not saved_data[user_id].get("account_locked", True)
        
        audit_log("ACCOUNT_UNLOCK", user_id, f"COMPLETED:was_locked={was_locked},now_unlocked={is_unlocked}")
        
        if not is_unlocked:
            # Save failed - try again
            USER_DATA[user_id]["account_locked"] = False
            save_user_data(USER_DATA)
            reload_user_data()
            is_unlocked = not USER_DATA[user_id].get("account_locked", True)
        
        return f"""✅ **Account unlocked successfully!**

Your account is now active. You can log in immediately.

🔓 Status: **Active**
👤 Student ID: **{user_id}**
🔍 Verification: Account is {'unlocked' if is_unlocked else 'still locked - please contact IT support'}

Try logging in now using the Test Login page!"""
    except Exception as e:
        return f"❌ Error unlocking account: {str(e)}\n\nPlease contact IT support."

def submit_mfa_reset(user_id: str, verified_fields: dict = None):
    """Reset MFA in the mock database after security verification"""
    # Reload data to get latest state
    reload_user_data()
    
    # Check if user exists
    if user_id not in USER_DATA:
        return f"❌ User ID {user_id} not found."
    
    # Verify security details if provided (extra check for MFA reset)
    if verified_fields:
        required_fields = ["full_name", "dob", "postcode", "phone"]
        for field in required_fields:
            if field not in verified_fields or not verified_fields[field]:
                continue  # Skip if field not provided
            if not verify_field(user_id, field, verified_fields[field]):
                return f"❌ Security verification failed. {field} does not match our records. Please contact IT support."
    
    # Reset MFA (unlock it)
    USER_DATA[user_id]["mfa_enabled"] = False
    save_user_data(USER_DATA)  # This will also reload the data
    
    # Verify the change was saved
    reload_user_data()
    is_mfa_disabled = not USER_DATA[user_id].get("mfa_enabled", True)
    
    user_email = USER_DATA[user_id].get("email", f"{user_id}@university.ac.uk")
    
    audit_log("MFA_RESET", user_id, "COMPLETED")
    
    return f"""✅ **MFA reset successful!**

Your Multi-Factor Authentication has been removed.

📱 Next Steps:
- Log in to your account
- You'll be prompted to set up MFA again
- Follow the on-screen instructions

🔍 Verification: MFA is {'disabled' if is_mfa_disabled else 'still enabled'}"""

# =====================
# AI (LANGUAGE ONLY)
# =====================
def get_ai_response(user_input: str, history: list) -> str:
    system_prompt = """
You are Querra, an AI IT support assistant for a university.

You can ONLY assist with:
- Password reset requests (guide users to self-service portal - DO NOT mention email)
- Account unlock requests
- MFA reset requests

CRITICAL RULES:
- You are ONLY responsible for conversation and gathering information
- You do NOT perform any actions (resets, unlocks, etc.)
- NEVER say "I've submitted" or "I've processed" or "request sent"
- NEVER mention "check your email" or "email sent" for password resets
- For password resets, DO NOT mention email - the system will guide them through the portal
- The SYSTEM handles all actions after identity verification
- Ask one question at a time
- Be friendly, professional, and concise
- Redirect non-login issues to IT support

After identity verification, simply ask the user what they need help with. Do not confirm actions or mention email.
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Audit Log", use_container_width=True):
            with open("audit.log", "w") as f:
                f.write("")
            st.success("✅ Audit log cleared!")
            st.rerun()
    
    with col2:
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
    page = st.radio("📍 Navigate", ["💬 Chat Support", "🔐 Test Login", "📊 Dashboard"], label_visibility="collapsed")
    
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
        # Check if user is asking to unlock account or reset password
        text_lower = user_input.lower()
        if any(word in text_lower for word in ["unlock", "locked", "lock", "account locked"]):
            # User wants to unlock - ask for student ID directly
            ai_reply = "I can help unlock your account. What is your **student ID**?"
            st.session_state.stage = "awaiting_user_id"
        elif any(word in text_lower for word in ["password", "reset", "forgot password", "password reset"]):
            # User wants password reset - ask for student ID directly
            ai_reply = "I can help guide you through the password reset process. What is your **student ID**?"
            st.session_state.stage = "awaiting_user_id"
        else:
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
            # Store verified fields for MFA reset verification
            if step == "full_name":
                st.session_state.verified_full_name = user_input
                st.session_state.verify_step = "postcode"
                ai_reply = "Thanks. What is your **postcode**?"
            elif step == "postcode":
                st.session_state.verified_postcode = user_input
                st.session_state.verify_step = "dob"
                ai_reply = "Great. What is your **date of birth**? (YYYY-MM-DD)"
            elif step == "dob":
                st.session_state.verified_dob = user_input
                st.session_state.verify_step = "phone"
                ai_reply = "Almost done. What is your **phone number**?"
            elif step == "phone":
                st.session_state.verified_phone = user_input
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

        # Execute the action directly based on keywords - be more aggressive with detection
        # For password reset, always show the guide directly - don't let AI respond
        if "password" in text or "reset" in text:
            ai_reply = submit_password_reset(user_id)
            ai_reply += "\n\n❓ **Were you able to access the portal and reset your password?** (Yes/No)"
            st.session_state.stage = "feedback"
        elif "unlock" in text or "locked" in text or "lock" in text:
            # Actually execute the unlock - don't just talk about it
            ai_reply = submit_account_unlock(user_id)
            ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
            st.session_state.stage = "feedback"
        elif "mfa" in text or "authenticat" in text or "multi" in text:
            # For MFA reset, use the verified fields from session state
            verified_fields = {
                "full_name": st.session_state.get("verified_full_name", ""),
                "dob": st.session_state.get("verified_dob", ""),
                "postcode": st.session_state.get("verified_postcode", ""),
                "phone": st.session_state.get("verified_phone", "")
            }
            ai_reply = submit_mfa_reset(user_id, verified_fields)
            ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
            st.session_state.stage = "feedback"
        else:
            # If unclear, ask AI to clarify but also check if they're trying to unlock
            # Sometimes users say "it's not unlocked" or "unlock my account" in different ways
            if any(word in text for word in ["unlock", "locked", "lock", "open", "access"]):
                ai_reply = submit_account_unlock(user_id)
                ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
                st.session_state.stage = "feedback"
            else:
                ai_reply = get_ai_response(user_input, st.session_state.history)
                # Don't change stage - stay in action to wait for clear choice

    elif stage == "feedback":
        user_id = st.session_state.user_id
        text_lower = user_input.lower()
        
        # Check what the last message was - was it password reset guide?
        last_message = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
        was_password_reset_question = "Were you able to access the portal" in last_message or "access the portal and reset your password" in last_message
        
        # Check if user is saying it's still locked/not working
        if any(phrase in text_lower for phrase in ["not unlocked", "still locked", "isn't unlocked", "hasn't unlocked", "didn't unlock"]):
            # Try unlocking again - maybe there was an issue
            ai_reply = "Let me try unlocking your account again...\n\n"
            ai_reply += submit_account_unlock(user_id)
            ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
            # Stay in feedback stage
        # Check if user says "no" to password reset portal question - they can't access it
        elif was_password_reset_question and ("no" in text_lower and len(text_lower.split()) <= 3):
            # User can't access the portal - create a ticket
            ticket_ref = f"QR-{user_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
            ai_reply = "I understand you're unable to access the password reset portal. Let me create a ticket for our IT support team to help you.\n\n"
            ai_reply += f"📋 **Ticket Reference**: **{ticket_ref}**\n\n"
            ai_reply += "**Issue**: Unable to access password reset portal\n"
            ai_reply += "**Student ID**: " + user_id + "\n"
            ai_reply += "**Registered Email**: " + USER_DATA[user_id].get("email", "N/A") + "\n"
            ai_reply += "**Phone**: " + USER_DATA[user_id].get("phone", "N/A") + "\n\n"
            ai_reply += "Our IT support team will review your case and help you reset your password. They'll contact you at your registered email or phone number.\n\n"
            ai_reply += "Is there anything else I can help you with?"
            audit_log("FEEDBACK", user_id, f"ESCALATED:{ticket_ref}:CANNOT_ACCESS_PORTAL")
            st.session_state.stage = "action"  # Stay in action in case they have more issues
        # Check if user can't access password reset portal (explicit phrases)
        elif any(phrase in text_lower for phrase in ["can't access", "cannot access", "unable to access", "can't get to", "link doesn't work", "portal doesn't work", "can't open", "website not working", "password reset not working", "can't reset", "unable to reset", "password is still not reset", "still not reset"]):
            # User can't access the portal - create a ticket
            ticket_ref = f"QR-{user_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
            ai_reply = "I understand you're unable to access the password reset portal or complete the reset. Let me create a ticket for our IT support team to help you.\n\n"
            ai_reply += f"📋 **Ticket Reference**: **{ticket_ref}**\n\n"
            ai_reply += "**Issue**: Unable to access password reset portal / Complete password reset\n"
            ai_reply += "**Student ID**: " + user_id + "\n"
            ai_reply += "**Registered Email**: " + USER_DATA[user_id].get("email", "N/A") + "\n"
            ai_reply += "**Phone**: " + USER_DATA[user_id].get("phone", "N/A") + "\n\n"
            ai_reply += "Our IT support team will review your case and help you reset your password. They'll contact you at your registered email or phone number.\n\n"
            ai_reply += "Is there anything else I can help you with?"
            audit_log("FEEDBACK", user_id, f"ESCALATED:{ticket_ref}:CANNOT_ACCESS_PORTAL")
            st.session_state.stage = "action"  # Stay in action in case they have more issues
        elif "yes" in text_lower or "all good" in text_lower or "solved" in text_lower or "fixed" in text_lower:
            # Check if they have other issues
            ai_reply = "Great! Is there anything else I can help you with today?\n\n"
            ai_reply += "• Password reset\n"
            ai_reply += "• Account unlock\n"
            ai_reply += "• MFA issues\n\n"
            ai_reply += "Or type 'no' if you're all set!"
            audit_log("FEEDBACK", user_id, "RESOLVED")
            st.session_state.stage = "action"  # Go back to action to handle follow-ups
        elif any(word in text_lower for word in ["password", "reset", "mfa", "authenticat", "unlock", "locked"]):
            # User has a follow-up issue - handle it
            text = text_lower
            if "password" in text or ("reset" in text and "password" in text):
                ai_reply = submit_password_reset(user_id)
                ai_reply += "\n\n❓ **Were you able to access the portal and reset your password?** (Yes/No)"
                st.session_state.stage = "feedback"
            elif "unlock" in text or "locked" in text or "lock" in text:
                ai_reply = submit_account_unlock(user_id)
                ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
                st.session_state.stage = "feedback"
            elif "mfa" in text or "authenticat" in text or "multi" in text:
                verified_fields = {
                    "full_name": st.session_state.get("verified_full_name", ""),
                    "dob": st.session_state.get("verified_dob", ""),
                    "postcode": st.session_state.get("verified_postcode", ""),
                    "phone": st.session_state.get("verified_phone", "")
                }
                ai_reply = submit_mfa_reset(user_id, verified_fields)
                ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
                st.session_state.stage = "feedback"
            else:
                ai_reply = get_ai_response(user_input, st.session_state.history)
                st.session_state.stage = "action"
        # Check for "no" response - handle based on context
        elif "no" in text_lower:
            # Check if this is in response to "anything else?" question
            if "else" in text_lower or "more" in text_lower or "other" in text_lower:
                # User says no more issues - end conversation
                ai_reply = "🎉 Great! Have a wonderful day, and happy studying!"
                audit_log("FEEDBACK", user_id, "RESOLVED")
                st.session_state.stage = "done"
            else:
                # Just "no" - might be response to password reset question (already handled above)
                # or might be ambiguous - ask for clarification
                ai_reply = "I understand you're having issues. Could you tell me what's not working?\n\n"
                ai_reply += "• Are you unable to access the password reset portal?\n"
                ai_reply += "• Is something else not working?\n\n"
                ai_reply += "If you can't access the portal, I can create a ticket for our IT team to help you."
                # Stay in feedback stage
        else:
            # User still has issues but didn't specify - ask what else they need
            # Check if they're asking for a ticket
            if any(phrase in text_lower for phrase in ["ticket", "escalate", "help desk", "support"]):
                # User wants a ticket or can't proceed - create one
                ticket_ref = f"QR-{user_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
                ai_reply = f"I'll create a ticket for our IT team to help you further.\n\n📋 **Ticket Reference**: **{ticket_ref}**\n\n"
                ai_reply += "Our IT support team will review your case and contact you. "
                ai_reply += "**Student ID**: " + user_id + "\n"
                ai_reply += "**Contact**: " + USER_DATA[user_id].get("email", "N/A") + "\n\n"
                ai_reply += "Is there anything else I can help you with while you wait?"
                audit_log("FEEDBACK", user_id, f"ESCALATED:{ticket_ref}")
                st.session_state.stage = "action"  # Stay in action in case they have more issues
            else:
                ai_reply = "I understand you're still having issues. Let me help you further.\n\n"
                ai_reply += "What else can I help you with?\n"
                ai_reply += "• Password reset (I'll guide you through the process step-by-step)\n"
                ai_reply += "• Account unlock\n"
                ai_reply += "• MFA issues\n\n"
                ai_reply += "Or if you can't access the portal or need more help, let me know and I'll create a ticket for our IT team."
                st.session_state.stage = "action"  # Go back to action stage

    else:
        # Catch-all: if user has been verified and is asking to unlock, do it
        if st.session_state.user_id and st.session_state.user_id in USER_DATA:
            text_lower = user_input.lower()
            # Check if they're asking to unlock
            if any(phrase in text_lower for phrase in ["unlock", "locked", "it's not unlocked", "still locked", "isn't unlocked"]):
                # They want to unlock - do it now
                ai_reply = submit_account_unlock(st.session_state.user_id)
                ai_reply += "\n\n❓ **Did this solve your issue?** (Yes/No)"
                st.session_state.stage = "feedback"
            else:
                ai_reply = get_ai_response(user_input, st.session_state.history)
        else:
            ai_reply = get_ai_response(user_input, st.session_state.history)

    # Save history
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": ai_reply})
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    with st.chat_message("assistant"):
        st.markdown(ai_reply)