import streamlit as st
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.error("❌ OPENROUTER_API_KEY not found. Check your .env file.")
    st.stop()

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
        respond("Hi there! What IT issue are you having today?")
        st.session_state.stage = "awaiting_issue"

    elif stage == "awaiting_issue":
        if "password" in user_input.lower():
            respond("Okay, let me check your account. Please provide your student ID (e.g., u12345).")
            st.session_state.stage = "awaiting_user_id"
        else:
            respond("I can only help with login-related issues like password resets, locked accounts, or MFA problems.")

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
        respond("Is there anything else I can help you with?")
