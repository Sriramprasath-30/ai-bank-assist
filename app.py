import streamlit as st
from datetime import datetime
import random

# --- Page Configuration ---
st.set_page_config(
    page_title="SecureBank AI Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- App Title ---
st.markdown('<h1 class="main-header">🏦 SecureBank AI Assistant</h1>', unsafe_allow_html=True)
st.markdown("### Your 24/7 Banking Support with Advanced Fraud Protection")

# --- Initialize Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Vizhibot Component ---
class Vizhibot:
    def __init__(self):
        self.state = "idle"
        self.last_animation = datetime.now()
    
    def display(self, state="idle", message=None):
        pass  # Placeholder for animation/state logic
    
    def chat_response(self, message):
        """Local responses only"""
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
        
        # Random fallback response
        fallback_responses = [
            "Can you please rephrase that?",
            "I am here to assist you with banking queries.",
            "Sorry, I didn't understand that. Ask about balance, loans, or transactions!"
        ]
        return ("🤖", random.choice(fallback_responses))

# Initialize Vizhibot
if "vizhibot" not in st.session_state:
    st.session_state.vizhibot = Vizhibot()

# --- Sidebar Module Selection ---
app_mode = st.sidebar.radio("Choose a module:", ["💬 Chat Support", "🔍 Fraud Detection", "💳 Make Payment", "📊 Account Dashboard"])

# --- Chat Support Module ---
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
    st.info("Demo mode: No real fraud detection implemented.")

# --- Make Payment Module ---
if app_mode == "💳 Make Payment":
    st.header("💳 Make Payment")
    st.markdown("Process payments securely through SecureBank AI Assistant.")
    st.info("Demo mode: No real payments implemented.")

# --- Account Dashboard Module ---
if app_mode == "📊 Account Dashboard":
    st.header("📊 Account Dashboard")
    st.markdown("Visualize your account activity, balance, and alerts.")
    st.info("Demo mode: No real account data available.")
