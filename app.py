import streamlit as st
import json
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

def get_ai_response(message, history=None):
    if not api_key:
        return "❌ API key not found. Please check your .env file."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if history is None:
        history = []

    messages = [{"role": "system", "content": "You are an IT support assistant helping users with login issues such as password resets, locked accounts, and MFA setup."}]
    messages += history
    messages.append({"role": "user", "content": message})

    data = {
        "model": "deepseek/deepseek-chat-v3",
        "messages": messages
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"❌ AI service error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Could not connect to the AI service: {e}"

# Load mock user data
try:
    with open("users.json") as f:
        user_data = json.load(f)
except FileNotFoundError:
    st.error("❌ Could not find users.json. Make sure it exists.")
    st.stop()

st.set_page_config(page_title="AI Self-Service Tool")
st.title("💬 AI Self-Service Login Assistant")

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "greeting"
    st.session_state.user_id = ""
    st.session_state.temp_data = {}
    st.session_state.identity_step = "full_name"  # for progressive checking

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def respond(message):
    st.session_state.messages.append({"role": "assistant", "content": message})
    with st.chat_message("assistant"):
        st.markdown(message)

# Show past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get user input
user_input = st.chat_input("Message the IT assistant...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    stage = st.session_state.stage

    if stage == "greeting":
        ai_reply = get_ai_response("Greet the user and ask how you can help.", st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "user", "content": "Start of conversation"})
        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
        respond(ai_reply)
        st.session_state.stage = "awaiting_issue"

    elif stage == "awaiting_issue":
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        ai_reply = get_ai_response(user_input, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
        respond(ai_reply)

        # Optional: route to ID check if AI suggests it
        if "student id" in ai_reply.lower() or "your id" in ai_reply.lower():
            st.session_state.stage = "awaiting_user_id"

    elif stage == "awaiting_user_id":
        user_id = user_input.strip()
        if user_id in user_data:
            st.session_state.user_id = user_id
            respond("Thanks. It looks like you've entered the wrong password too many times. Have you forgotten your password? (yes/no)")
            st.session_state.stage = "awaiting_forgot_password"
        else:
            respond("I couldn't find that student ID. Please try again.")

    elif stage == "awaiting_forgot_password":
        if user_input.lower() == "no":
            respond("Okay, I’ve unlocked your account. Please try logging in again.")
            st.session_state.stage = "done"
        elif user_input.lower() == "yes":
            respond("Let’s reset your password. First, please provide your full name.")
            st.session_state.stage = "verifying_identity"
            st.session_state.identity_step = "full_name"
        else:
            respond("Please reply with 'yes' or 'no'.")

    elif stage == "verifying_identity":
        current_step = st.session_state.identity_step
        value = user_input.strip()
        st.session_state.temp_data[current_step] = value
        record = user_data[st.session_state.user_id]

        def next_prompt(next_step, prompt_text):
            st.session_state.identity_step = next_step
            respond(prompt_text)

        if current_step == "full_name":
            if value.lower() == record["full_name"].lower():
                next_prompt("postcode", "Thanks. Now, what is your postcode?")
            else:
                respond("❌ Name doesn't match our records. Please contact the IT service desk.")
                st.session_state.stage = "done"

        elif current_step == "postcode":
            if value.lower() == record["postcode"].lower():
                next_prompt("dob", "What is your date of birth? (YYYY-MM-DD)")
            else:
                respond("❌ Postcode doesn't match our records. Please contact the IT service desk.")
                st.session_state.stage = "done"

        elif current_step == "dob":
            if value == record["dob"]:
                next_prompt("phone", "Finally, what is your phone number?")
            else:
                respond("❌ Date of birth doesn't match our records. Please contact the IT service desk.")
                st.session_state.stage = "done"

        elif current_step == "phone":
            if value == record["phone"]:
                respond("✅ Identity verified. Please provide a mobile number where we can send your new password.")
                st.session_state.stage = "awaiting_mobile"
            else:
                respond("❌ Phone number doesn't match our records. Please contact the IT service desk.")
                st.session_state.stage = "done"

    elif stage == "awaiting_mobile":
        phone = user_input.strip()
        respond(f"✅ Password reset to `TempPass123!`. A text message has been sent to {phone}.")
        st.session_state.stage = "done"

    elif stage == "done":
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        ai_reply = get_ai_response(user_input, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
        respond(ai_reply)
