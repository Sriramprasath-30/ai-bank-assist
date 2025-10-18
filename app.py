import streamlit as st
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import random
import openai  # New: OpenAI SDK
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="SecureBank AI Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
/* Your existing CSS here (same as before) */
</style>
""", unsafe_allow_html=True)

# --- App Title ---
st.markdown('<h1 class="main-header">🏦 SecureBank AI Assistant</h1>', unsafe_allow_html=True)
st.markdown("### Your 24/7 Banking Support with Advanced Fraud Protection")

# --- Initialize Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "transaction_history" not in st.session_state:
    st.session_state.transaction_history = []

if "alerts" not in st.session_state:
    st.session_state.alerts = []

# --- Initialize OpenAI ---
# Store your OpenAI API key in Streamlit Secrets
openai.api_key = st.secrets["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"]  # OR use os.environ.get("OPENAI_API_KEY")

def ask_openai(prompt, model="gpt-3.5-turbo", max_tokens=200):
    """Call OpenAI API to get a response"""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful banking assistant named Vizhibot."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        return f"Error connecting to OpenAI: {e}"

# --- Vizhibot Component (same as before) ---
class Vizhibot:
    def __init__(self):
        self.state = "idle"
        self.last_animation = datetime.now()
    
    def display(self, state="idle", message=None):
        # Placeholder for animation/state logic
        pass
    
    def random_idle_animation(self):
        # Placeholder for random idle animations
        pass
    
    def chat_response(self, message):
        """Now uses OpenAI"""
        # Predefined responses
        predefined_responses = {
            "balance": ("💰", "Looking up your account balance..."),
            "loan": ("🤔", "Checking loan options for you..."),
            "fraud": ("🛡️", "Investigating security matters..."),
            "transaction": ("🔍", "Analyzing transaction patterns..."),
            "help": ("🤖", "I'm here to help! What do you need?"),
            "thank": ("😊", "You're welcome! Happy to assist!"),
            "hello": ("👋", "Hello! I'm Vizhibot, your banking assistant!"),
            "bye": ("👋", "Goodbye! Stay secure!")
        }
        
        for key, (emoji, response) in predefined_responses.items():
            if key in message.lower():
                return (emoji, response)
        
        # Otherwise, ask OpenAI
        answer = ask_openai(message)
        return ("🤖", answer)

# Initialize Vizhibot
if "vizhibot" not in st.session_state:
    st.session_state.vizhibot = Vizhibot()

# --- The rest of your app remains mostly unchanged ---
# Sidebar, SpendingProfile, Fraud Detection, Payments, Dashboard

# --- Example Chat Support with OpenAI ---
app_mode = st.sidebar.radio("Choose a module:", ["💬 Chat Support", "🔍 Fraud Detection", "💳 Make Payment", "📊 Account Dashboard"])

if app_mode == "💬 Chat Support":
    st.header("💬 AI Customer Support")
    
    # Introduction
    if not st.session_state.chat_history:
        intro_message = "Namaste! I'm Vizhibot, your AI-powered banking assistant. Ask me anything about banking, loans, or transactions!"
        st.session_state.chat_history.append(("assistant", intro_message))
    
    for speaker, message in st.session_state.chat_history:
        if speaker == "user":
            st.chat_message("user").markdown(f"**You:** {message}")
        else:
            st.chat_message("assistant").markdown(f"**Vizhibot:** {message}")
    
    if prompt := st.chat_input("Ask me about banking, fraud detection, or account help..."):
        st.session_state.chat_history.append(("user", prompt))
        st.session_state.vizhibot.display("thinking", "Processing your question...")
        
        emoji, response = st.session_state.vizhibot.chat_response(prompt)
        st.session_state.chat_history.append(("assistant", response))
        st.rerun()

# --- Fraud Detection Module ---
if app_mode == "🔍 Fraud Detection":
    st.header("🔍 Fraud Detection")
    st.markdown("This module analyzes transactions to detect potential frauds.")
    # ... your fraud detection code here ...

# --- Make Payment Module ---
if app_mode == "💳 Make Payment":
    st.header("💳 Make Payment")
    st.markdown("Process payments securely through SecureBank AI Assistant.")
    # ... your payment processing code here ...

# --- Account Dashboard Module ---
if app_mode == "📊 Account Dashboard":
    st.header("📊 Account Dashboard")
    st.markdown("Visualize your account activity, balance, and alerts.")
    # ... your dashboard code here ...

# --- End of App ---
