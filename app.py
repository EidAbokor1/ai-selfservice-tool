import streamlit as st
import json
from dotenv import load_dotenv
import os
import requests
from typing import Dict, Any

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

def load_user_data() -> Dict[str, Any]:
    """Load mock user data from JSON file"""
    try:
        with open("users.json") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Could not find users.json. Make sure it exists.")
        st.stop()

def get_ai_response(user_input: str, chat_history: list = None) -> str:
    """Get AI response for IT support queries"""
    if not api_key:
        return "❌ API key not found. Please check your .env file."

    if chat_history is None:
        chat_history = []

    # Load user data to provide context to AI
    user_data = load_user_data()
    
    # Create system prompt with user database context
    system_prompt = f"""You are an AI IT support assistant for a university. You can help with:
1. Password resets
2. Account unlocks  
3. MFA (Multi-Factor Authentication) resets

IMPORTANT RULES:
- Only help with login-related issues (password, locked accounts, MFA)
- For anything else, politely redirect to IT desk
- Be friendly, professional, and secure
- Always verify user identity before making changes

USER DATABASE (for verification):
{json.dumps(user_data, indent=2)}

PROCESS:
1. Greet users and ask what they need help with
2. If it's a login issue, ask for their student ID
3. Verify their identity by asking for personal details (full name, postcode, DOB, phone)
4. Only proceed with help after successful verification
5. For password reset: Set temporary password "TempPass123!" and mention SMS sent
6. For account unlock: Simply unlock the account
7. For MFA reset: Reset their MFA and ask them to set it up again

Always verify identity step by step. Don't accept all details at once."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_input})

    data = {
        "model": "deepseek/deepseek-chat-v3",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 500
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"❌ AI service error: {response.status_code} - {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"❌ Could not connect to the AI service: {e}"

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="AI IT Support",
        page_icon="💬",
        layout="centered"
    )
    
    st.title("💬 AI IT Support Assistant")
    st.markdown("*Get help with password resets, locked accounts, and MFA issues*")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "👋 Hello! I'm your AI IT assistant. I can help with:\n\n• **Password resets**\n• **Locked accounts**\n• **MFA (Multi-Factor Authentication) issues**\n\nWhat can I help you with today?"
            }
        ]
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if user_input := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = get_ai_response(user_input, st.session_state.chat_history)
            st.markdown(ai_response)

        # Add to chat history and session
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # Sidebar with info
    with st.sidebar:
        st.markdown("### 🔧 Available Services")
        st.markdown("""
        - 🔑 **Password Reset**
        - 🔓 **Account Unlock** 
        - 📱 **MFA Reset**
        """)
        
        st.markdown("### 📋 What You'll Need")
        st.markdown("""
        - Student ID
        - Full name
        - Postcode
        - Date of birth
        - Phone number
        """)
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = [
                {
                    "role": "assistant", 
                    "content": "👋 Hello! I'm your AI IT assistant. I can help with:\n\n• **Password resets**\n• **Locked accounts**\n• **MFA (Multi-Factor Authentication) issues**\n\nWhat can I help you with today?"
                }
            ]
            st.session_state.chat_history = []
            st.rerun()

if __name__ == "__main__":
    main()