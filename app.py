import streamlit as st
from transformers import pipeline
import joblib
import numpy as np
import pandas as pd
import sqlite3
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import random
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="SecureBank AI Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS with Vizhibot Animations ---
st.markdown("""
<style>
    .main-header { font-size: 3rem; color: #1e3a8a; }
    .stButton>button { width: 100%; border-radius: 8px; }
    .stAlert { border-radius: 10px; }
    .transaction-box { border: 1px solid #ccc; padding: 20px; border-radius: 10px; margin: 10px 0; }
    .risk-low { color: #00cc00; font-weight: bold; }
    .risk-medium { color: #ff9900; font-weight: bold; }
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .xai-breakdown { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0; }
    
    /* Vizhibot Animation Styles */
    .vizhibot-container {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    
    .vizhibot {
        font-size: 3rem;
        transition: all 0.3s ease;
        position: relative;
    }
    
    /* Animations */
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes thinking {
        0%, 100% { transform: rotate(0deg); }
        25% { transform: rotate(5deg); }
        75% { transform: rotate(-5deg); }
    }
    
    @keyframes celebrate {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    
    @keyframes worried {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    @keyframes processing {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .vizhibot-bounce { animation: bounce 1s infinite; }
    .vizhibot-thinking { animation: thinking 1.5s infinite; }
    .vizhibot-celebrate { animation: celebrate 0.5s infinite; }
    .vizhibot-worried { animation: worried 0.8s infinite; }
    .vizhibot-processing { animation: processing 2s linear infinite; }
    
    .vizhibot-message {
        background: #f0f2f6;
        padding: 12px;
        border-radius: 15px;
        margin: 10px 0;
        border-left: 4px solid #1e3a8a;
        font-style: italic;
    }
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

# --- Initialize Groq Client ---
@st.cache_resource
def initialize_groq():
    """Initialize Groq client with API key"""
    api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.warning("⚠️ GROQ_API_KEY not found. Please add it to your Streamlit secrets.")
        return None
    try:
        client = Groq(api_key=api_key)
        # Test the connection
        test_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        return client
    except Exception as e:
        st.error(f"Failed to initialize Groq: {str(e)}")
        return None

groq_client = initialize_groq()

# --- Vizhibot Component ---
class Vizhibot:
    def __init__(self):
        self.state = "idle"
        self.last_animation = datetime.now()
    
    def display(self, state="idle", message=None):
        """Display Vizhibot with specified animation state"""
        self.state = state
        self.last_animation = datetime.now()
        
        # Map states to emojis and animations
        states = {
            "idle": {"emoji": "🤖", "animation": "vizhibot-bounce", "title": "Vizhibot is ready!"},
            "thinking": {"emoji": "🤔", "animation": "vizhibot-thinking", "title": "Vizhibot is thinking..."},
            "processing": {"emoji": "⚙️", "animation": "vizhibot-processing", "title": "Processing your request"},
            "success": {"emoji": "✅", "animation": "vizhibot-celebrate", "title": "Success!"},
            "warning": {"emoji": "⚠️", "animation": "vizhibot-worried", "title": "Warning detected"},
            "error": {"emoji": "❌", "animation": "vizhibot-worried", "title": "Error occurred"},
            "celebrate": {"emoji": "🎉", "animation": "vizhibot-celebrate", "title": "Celebration time!"},
            "analyzing": {"emoji": "🔍", "animation": "vizhibot-thinking", "title": "Analyzing patterns..."},
            "security": {"emoji": "🛡️", "animation": "vizhibot-bounce", "title": "Security check"},
            "money": {"emoji": "💰", "animation": "vizhibot-celebrate", "title": "Money matters!"}
        }
        
        current_state = states.get(state, states["idle"])
        
        # Create Vizhibot display
        vizhibot_html = f"""
        <div class="vizhibot-container">
            <div class="vizhibot {current_state['animation']}" title="{current_state['title']}">
                {current_state['emoji']}
            </div>
        </div>
        """
        
        if message:
            vizhibot_html += f'<div class="vizhibot-message">💬 {message}</div>'
        
        st.markdown(vizhibot_html, unsafe_allow_html=True)
        return current_state
    
    def random_idle_animation(self):
        """Random idle animation to keep Vizhibot lively"""
        if (datetime.now() - self.last_animation).seconds > 10:
            animations = ["bounce", "thinking", "celebrate"]
            random_anim = random.choice(animations)
            self.display(random_anim)
    
    def chat_response(self, message):
        """Vizhibot responds in chat with appropriate animation"""
        responses = {
            "balance": ("💰", "Looking up your account balance..."),
            "loan": ("🤔", "Checking loan options for you..."),
            "fraud": ("🛡️", "Investigating security matters..."),
            "transaction": ("🔍", "Analyzing transaction patterns..."),
            "help": ("🤖", "I'm here to help! What do you need?"),
            "thank": ("😊", "You're welcome! Happy to assist!"),
            "hello": ("👋", "Hello! I'm Vizhibot, your banking assistant!"),
            "bye": ("👋", "Goodbye! Stay secure!")
        }
        
        for key, (emoji, response) in responses.items():
            if key in message.lower():
                return (emoji, response)
        
        return ("🤖", "I'm analyzing your request...")

# Initialize Vizhibot
if "vizhibot" not in st.session_state:
    st.session_state.vizhibot = Vizhibot()

# --- Known Fraudulent Merchants Database ---
FRAUDULENT_MERCHANTS = {
    "QuickCash Now": {"risk_score": 0.8, "reports": 42, "last_reported": "2025-08-15"},
    "CryptoInvest Pro": {"risk_score": 0.7, "reports": 28, "last_reported": "2025-08-20"},
    "Global Deals LLC": {"risk_score": 0.9, "reports": 57, "last_reported": "2025-08-10"},
    "Discount Electronics": {"risk_score": 0.6, "reports": 19, "last_reported": "2025-08-18"},
    "Luxury Watches Direct": {"risk_score": 0.75, "reports": 35, "last_reported": "2025-08-22"}
}

# --- Unique Feature 1: Spending Profile AI ---
class SpendingProfile:
    def __init__(self):
        self.transaction_history = []
        self.weekly_spending = 0
        self.typical_spending = {
            'morning': {'amount': 1500, 'count': 0},
            'afternoon': {'amount': 2500, 'count': 0},
            'evening': {'amount': 3500, 'count': 0},
            'night': {'amount': 2000, 'count': 0}
        }
        self.category_patterns = {}
        self.last_updated = datetime.now()
    
    def learn_from_transaction(self, amount, category, hour):
        """AI learns from each transaction to build spending profile"""
        transaction = {
            'amount': amount,
            'category': category,
            'hour': hour,
            'timestamp': datetime.now(),
            'day_of_week': datetime.now().weekday()
        }
        self.transaction_history.append(transaction)
        
        time_period = self._get_time_period(hour)
        self.typical_spending[time_period]['amount'] = (
            self.typical_spending[time_period]['amount'] + amount
        ) / 2
        self.typical_spending[time_period]['count'] += 1
        
        if category not in self.category_patterns:
            self.category_patterns[category] = {'total': 0, 'count': 0}
        self.category_patterns[category]['total'] += amount
        self.category_patterns[category]['count'] += 1
        
        one_week_ago = datetime.now() - timedelta(days=7)
        self.weekly_spending = sum(t['amount'] for t in self.transaction_history 
                                 if t['timestamp'] > one_week_ago)
    
    def _get_time_period(self, hour):
        if 5 <= hour < 12: return 'morning'
        elif 12 <= hour < 17: return 'afternoon'
        elif 17 <= hour < 22: return 'evening'
        else: return 'night'
    
    def calculate_behavior_risk(self, amount, category, hour):
        """Calculate how unusual this transaction is for this user"""
        risks = []
        risk_factors = []
        
        time_period = self._get_time_period(hour)
        typical_amount = self.typical_spending[time_period]['amount']
        if typical_amount > 0:
            amount_ratio = amount / typical_amount
            if amount_ratio > 3.0:
                risk_score = min(0.6 + (amount_ratio - 3.0) * 0.1, 0.9)
                risks.append(risk_score)
                risk_factors.append((
                    f"Amount is {amount_ratio:.1f}x your {time_period} average", 
                    risk_score
                ))
            elif amount_ratio > 2.0:
                risk_score = min(0.4 + (amount_ratio - 2.0) * 0.2, 0.6)
                risks.append(risk_score)
                risk_factors.append((
                    f"Large amount for {time_period} ({amount_ratio:.1f}x average)", 
                    risk_score
                ))
        
        if category in self.category_patterns:
            avg_category = self.category_patterns[category]['total'] / self.category_patterns[category]['count']
            if amount > avg_category * 4:
                risk_score = min(0.7 + (amount / avg_category - 4) * 0.05, 0.9)
                risks.append(risk_score)
                risk_factors.append((
                    f"Unusually large for {category} ({amount/avg_category:.1f}x average)", 
                    risk_score
                ))
            elif amount > avg_category * 2:
                risk_score = min(0.4 + (amount / avg_category - 2) * 0.15, 0.7)
                risks.append(risk_score)
                risk_factors.append((
                    f"Large for {category} ({amount/avg_category:.1f}x average)", 
                    risk_score
                ))
        else:
            risks.append(0.3)
            risk_factors.append(("New spending category", 0.3))
        
        if self.weekly_spending + amount > 50000:
            overspend_ratio = (self.weekly_spending + amount) / 50000
            risk_score = min(0.5 + (overspend_ratio - 1) * 0.5, 0.9)
            risks.append(risk_score)
            risk_factors.append((
                f"Exceeds weekly spending pattern ({overspend_ratio:.1f}x limit)", 
                risk_score
            ))
        
        if not risks:
            return 0.1, ["Normal spending pattern"], []
        
        max_risk = max(risks) if risks else 0
        avg_risk = sum(risks) / len(risks) if risks else 0
        total_risk = max_risk * 0.7 + avg_risk * 0.3
        
        return min(total_risk, 0.95), risk_factors

# Initialize user spending profile
if "spending_profile" not in st.session_state:
    st.session_state.spending_profile = SpendingProfile()
    typical_transactions = [
        (2500, "Restaurant", 19),
        (5000, "Online Shopping", 20),
        (1500, "Coffee", 8),
        (8000, "Electronics", 15),
        (2000, "Groceries", 18),
        (1000, "Transport", 9),
        (4000, "Entertainment", 21)
    ]
    for amount, category, hour in typical_transactions:
        st.session_state.spending_profile.learn_from_transaction(amount, category, hour)

# --- Sidebar for Navigation ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3698/3698156.png", width=100)
    st.title("Navigation")
    app_mode = st.radio("Choose a module:", 
                       ["💬 Chat Support", "🔍 Fraud Detection", "💳 Make Payment", "📊 Account Dashboard"])
    
    st.divider()
    st.header("Account Overview")
    st.metric("Available Balance", "₹82,450")
    st.metric("Total Assets", "₹3,45,320")
    if hasattr(st.session_state, 'spending_profile'):
        st.metric("Weekly Spending", f"₹{st.session_state.spending_profile.weekly_spending:,.0f}")
    
    if groq_client:
        st.success("🤖 Groq AI Enhanced Mode")
        st.caption("Powered by Llama 3.1")
    else:
        st.warning("🔧 Standard Mode")
        st.caption("Add GROQ_API_KEY to enable AI")
    
    if st.session_state.alerts:
        st.divider()
        st.header("🔔 Alerts")
        for i, alert in enumerate(st.session_state.alerts[-3:]):
            st.warning(f"{alert['type']}: {alert['message']}")
            if st.button(f"Dismiss", key=f"dismiss_{i}"):
                st.session_state.alerts.pop(i)
                st.rerun()

# --- Load AI Models ---
@st.cache_resource
def load_models():
    try:
        qa_model = pipeline("question-answering")
    except:
        qa_model = None
    
    try:
        fraud_model = joblib.load('fraud_model.pkl')
    except:
        fraud_model = None
    
    return qa_model, fraud_model

qa_model, fraud_model = load_models()

# --- Banking Knowledge Base ---
banking_context = """SecureBank offers comprehensive financial services including savings accounts, loans, and investment products.
Our customer support is available 24/7 at 1-800-SECURE-BANK (1-800-732-8732).
Personal loan interest rates start at 8.5% APR based on creditworthiness.
Savings accounts earn 3.2% APY with a minimum balance of ₹5000.
To apply for any loan product, you'll need government-issued ID, proof of address, and recent income verification.
The daily ATM withdrawal limit is ₹50,000 for most account types.
The maximum mobile check deposit is ₹25,000 per day.
If you suspect fraudulent activity, immediately call our security team at 1-800-732-8732.
Fixed term deposits require a minimum of ₹25,000 for 12-month terms earning 4.5% APY.
We have over 200 branches across major Indian cities."""

# --- Groq Integration Functions ---
def get_groq_response(user_query, conversation_history=None):
    """Get intelligent response from Groq with banking context"""
    if not groq_client:
        if qa_model:
            try:
                result = qa_model(question=user_query, context=banking_context)
                return result['answer'] if result['score'] > 0.2 else "I'm not sure about that. Please contact our support team."
            except:
                return "I'm having trouble connecting to the knowledge base."
        return "AI service temporarily unavailable. Please contact support."
    
    try:
        messages = [
            {
                "role": "system",
                "content": f"""You are Vizhibot, an AI banking assistant for SecureBank. 

Your personality:
- Friendly, professional, and helpful
- Security-conscious and trustworthy
- Use emojis sparingly but appropriately
- Keep responses concise but informative
- Always prioritize customer security

Banking context:
{banking_context}

Key capabilities:
1. Answer banking questions (accounts, loans, rates)
2. Fraud detection and security alerts
3. Transaction analysis
4. Financial guidance
5. Account management support

Important security protocols:
- Never ask for passwords or PINs
- Always direct urgent fraud cases to: 1-800-732-8732
- Encourage 2FA for suspicious activities
- Verify identity for sensitive operations

Response guidelines:
- Keep answers under 150 words unless detailed explanation needed
- Use INR (₹) for currency
- Provide actionable next steps
- If unsure, direct to human support"""
            }
        ]
        
        if conversation_history:
            for speaker, message in conversation_history[-6:]:
                role = "user" if speaker == "user" else "assistant"
                messages.append({"role": role, "content": message})
        
        messages.append({"role": "user", "content": user_query})
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=300,
            top_p=0.9,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        if qa_model:
            try:
                result = qa_model(question=user_query, context=banking_context)
                return result['answer'] if result['score'] > 0.2 else "I'm having trouble right now. Please try again."
            except:
                pass
        return f"I'm experiencing technical difficulties. Please try again or contact support."

def get_fraud_explanation(transaction_data, risk_score, risk_factors):
    """Get natural language explanation of fraud analysis using Groq"""
    if not groq_client:
        return None
    
    try:
        factors_text = "\n".join([
            f"- {factor}: {score:.0%} - {explanation}" 
            for factor, score, explanation in risk_factors
        ])
        
        prompt = f"""As a fraud detection expert, explain this transaction analysis to a customer:

Transaction Details:
- Amount: ₹{transaction_data['amount']:,.2f}
- Time: {transaction_data['hour']}:00
- Merchant: {transaction_data['merchant']}
- Risk Score: {risk_score:.0%}

Risk Factors Detected:
{factors_text}

Provide:
1. Clear summary of the risk level (2-3 sentences)
2. Main concerns identified
3. Recommended action for the customer

Keep it under 100 words, customer-friendly, and actionable."""

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a fraud prevention expert explaining risks clearly to customers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=250
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return None

def get_spending_insights(spending_profile):
    """Generate personalized spending insights using Groq"""
    if not groq_client or not spending_profile.transaction_history:
        return None
    
    try:
        total_spent = sum(t['amount'] for t in spending_profile.transaction_history[-30:])
        categories = {}
        for t in spending_profile.transaction_history[-30:]:
            cat = t.get('category', 'Other')
            categories[cat] = categories.get(cat, 0) + t['amount']
        
        categories_text = "\n".join([
            f"- {cat}: ₹{amt:,.2f}" 
            for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True)
        ])
        
        prompt = f"""Analyze this customer's spending and provide 3 personalized insights:

30-Day Spending Summary:
- Total: ₹{total_spent:,.2f}
- Weekly Average: ₹{spending_profile.weekly_spending:,.2f}
- Transactions: {len(spending_profile.transaction_history[-30:])}

Category Breakdown:
{categories_text}

Provide:
1. One positive observation
2. One area for potential savings
3. One security or budget tip

Keep each insight to 1 sentence. Be encouraging and practical."""

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a friendly financial advisor providing helpful spending insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return None
# --- Vizhibot Introduction ---
def get_vizhibot_introduction():
    """Return Vizhibot's introduction and capabilities"""
    return """
**Namaste! I'm Vizhibot, your AI-powered banking assistant.** 👁️

I'm here to help you with all your banking needs. Here's what I can do:

💬 **Answer Questions**: I can help with account information, loan details, interest rates, and banking policies.

🔍 **Fraud Detection**: I analyze transactions in real-time to protect you from fraudulent activities.

💳 **Payment Monitoring**: I assess risks before payments are processed to keep your money safe.

📊 **Financial Insights**: I provide spending analysis and help you understand your financial patterns.

🛡️ **Security Alerts**: I notify you immediately of any suspicious activities on your account.

How can I assist you today?
    """

# --- Enhanced Fraud Detection Function with XAI ---
def analyze_transaction(amount, hour, merchant):
    """Analyze transaction with explainable AI components"""
    risk_factors = []
    total_risk = 0
    
    if merchant in FRAUDULENT_MERCHANTS:
        merchant_risk = FRAUDULENT_MERCHANTS[merchant]["risk_score"]
        risk_factors.append((
            f"Known risky merchant ({merchant})", 
            merchant_risk,
            f"This merchant has {FRAUDULENT_MERCHANTS[merchant]['reports']} fraud reports"
        ))
        total_risk = max(total_risk, merchant_risk)
    
    if fraud_model is not None:
        try:
            amount_to_hour_ratio = amount / (hour + 1)
            input_features = np.array([[amount, hour, amount_to_hour_ratio]])
            
            prediction = fraud_model.predict(input_features)[0]
            probability = fraud_model.predict_proba(input_features)[0][1]
            
            if probability > 0.3:
                risk_factors.append((
                    "ML Model Detection", 
                    probability,
                    "AI model identified suspicious patterns"
                ))
                total_risk = max(total_risk, probability)
        except Exception as e:
            risk_factors.append(("Model Error", 0.2, f"Prediction error: {str(e)}"))
    
    if amount > 15000:
        amount_risk = min(0.3 + (amount - 15000) / 50000, 0.8)
        risk_factors.append((
            f"High amount (₹{amount:,.0f})", 
            amount_risk,
            "Transaction amount is significantly above average"
        ))
        total_risk = max(total_risk, amount_risk)
    
    if hour < 6 or hour > 22:
        time_risk = 0.5 if hour < 6 else 0.4
        risk_factors.append((
            f"Unusual time ({hour}:00)", 
            time_risk,
            "Transaction occurred during non-typical hours"
        ))
        total_risk = max(total_risk, time_risk)
    
    if risk_factors:
        sorted_factors = sorted(risk_factors, key=lambda x: x[1], reverse=True)
        total_risk = sorted_factors[0][1] * 0.7
        if len(sorted_factors) > 1:
            total_risk += sum(f[1] for f in sorted_factors[1:]) / len(sorted_factors[1:]) * 0.3
        
        total_risk = min(total_risk, 0.95)
    
    return total_risk, risk_factors

# --- Predictive Risk Engine ---
def predict_payment_risk(amount, category, hour, merchant):
    """Predict risk before payment is processed"""
    behavior_risk, behavior_factors = st.session_state.spending_profile.calculate_behavior_risk(amount, category, hour)
    
    fraud_risk, fraud_factors = analyze_transaction(amount, hour, merchant)
    
    all_factors = []
    
    for factor, score in behavior_factors:
        all_factors.append((f"Behavior: {factor}", score * 0.7, "Based on your spending patterns"))
    
    for factor, score, explanation in fraud_factors:
        all_factors.append((factor, score, explanation))
    
    if all_factors:
        total_risk = sum(score for _, score, _ in all_factors) / len(all_factors)
    else:
        total_risk = 0.1
    
    return total_risk, all_factors

# --- Anomaly Detection Function ---
def detect_spending_anomalies():
    """Detect anomalies in spending patterns"""
    if not hasattr(st.session_state, 'spending_profile') or not st.session_state.spending_profile.transaction_history:
        return [], []
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_transactions = [
        t for t in st.session_state.spending_profile.transaction_history 
        if t['timestamp'] > thirty_days_ago
    ]
    
    if len(recent_transactions) < 5:
        return [], []
    
    amounts = [t['amount'] for t in recent_transactions]
    mean = np.mean(amounts)
    std = np.std(amounts)
    
    anomalies = []
    for i, transaction in enumerate(recent_transactions):
        z_score = abs(transaction['amount'] - mean) / std if std > 0 else 0
        if z_score > 2.0:
            anomalies.append({
                'index': i,
                'transaction': transaction,
                'z_score': z_score,
                'deviation': f"{z_score:.1f} standard deviations from mean"
            })
    
    return recent_transactions, anomalies

# --- Alert System ---
def add_alert(alert_type, message):
    """Add an alert to the system"""
    alert = {
        'type': alert_type,
        'message': message,
        'timestamp': datetime.now(),
        'read': False
    }
    st.session_state.alerts.append(alert)
    
    if alert_type == "Fraud Alert":
        pass

# --- MODULE 1: Chat Support ---
if app_mode == "💬 Chat Support":
    st.session_state.vizhibot.display("idle", "Ready to assist you!")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("💬 Chat with Vizhibot")
        
        chat_container = st.container()
        with chat_container:
            if not st.session_state.chat_history:
                st.info(get_vizhibot_introduction())
            else:
                for speaker, message in st.session_state.chat_history:
                    if speaker == "user":
                        st.markdown(f"**You:** {message}")
                    else:
                        st.markdown(f"**Vizhibot:** {message}")
        
        user_input = st.text_input("Ask me anything about banking:", key="chat_input", placeholder="e.g., What are your loan rates?")
        
        col_send, col_clear = st.columns([1, 1])
        
        with col_send:
            if st.button("Send", type="primary", use_container_width=True):
                if user_input:
                    st.session_state.chat_history.append(("user", user_input))
                    st.session_state.vizhibot.display("thinking", "Processing your question...")
                    response = get_groq_response(user_input, st.session_state.chat_history)
                    st.session_state.chat_history.append(("assistant", response))
                    st.rerun()
        
        with col_clear:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
    
    with col2:
        st.subheader("Quick Actions")
        if st.button("💰 Check Balance", use_container_width=True):
            st.session_state.chat_history.append(("user", "What's my account balance?"))
            response = "Your current account balance is ₹82,450. You have ₹3,45,320 in total assets across all accounts."
            st.session_state.chat_history.append(("assistant", response))
            st.rerun()
        
        if st.button("🏠 Loan Options", use_container_width=True):
            st.session_state.chat_history.append(("user", "What loan options are available?"))
            response = get_groq_response("What loan options are available?", st.session_state.chat_history)
            st.session_state.chat_history.append(("assistant", response))
            st.rerun()
        
        if st.button("🛡️ Security Tips", use_container_width=True):
            st.session_state.chat_history.append(("user", "Give me security tips"))
            response = get_groq_response("Give me important security tips for online banking", st.session_state.chat_history)
            st.session_state.chat_history.append(("assistant", response))
            st.rerun()
        
        if st.button("📞 Contact Support", use_container_width=True):
            st.info("📞 Call: 1-800-732-8732\n📧 Email: support@securebank.com\n⏰ Available 24/7")

# --- MODULE 2: Fraud Detection ---
elif app_mode == "🔍 Fraud Detection":
    st.session_state.vizhibot.display("security", "Running security analysis...")
    
    st.subheader("🔍 Real-Time Fraud Detection System")
    
    tab1, tab2, tab3 = st.tabs(["🔎 Analyze Transaction", "📊 Spending Anomalies", "🛡️ Security Dashboard"])
    
    with tab1:
        st.markdown("### Analyze a Transaction for Fraud Risk")
        
        col1, col2 = st.columns(2)
        
        with col1:
            amount = st.number_input("Transaction Amount (₹)", min_value=0.0, value=5000.0, step=100.0)
            merchant = st.text_input("Merchant Name", value="Amazon India")
            category = st.selectbox("Category", ["Online Shopping", "Restaurant", "Groceries", "Electronics", 
                                                 "Entertainment", "Transport", "Healthcare", "Other"])
        
        with col2:
            hour = st.slider("Transaction Hour", 0, 23, 14)
            st.info(f"🕐 Selected time: {hour}:00 ({('Morning' if 5<=hour<12 else 'Afternoon' if 12<=hour<17 else 'Evening' if 17<=hour<22 else 'Night')})")
        
        if st.button("🔍 Analyze Transaction", type="primary", use_container_width=True):
            st.session_state.vizhibot.display("analyzing", "Scanning for fraud patterns...")
            
            with st.spinner("Analyzing transaction..."):
                time.sleep(1)
                
                risk_score, risk_factors = predict_payment_risk(amount, category, hour, merchant)
                
                st.markdown("---")
                st.markdown("### 📊 Analysis Results")
                
                col_risk, col_status = st.columns([1, 2])
                
                with col_risk:
                    st.metric("Risk Score", f"{risk_score:.0%}")
                    
                    if risk_score < 0.3:
                        st.success("✅ Low Risk")
                        st.session_state.vizhibot.display("success", "Transaction looks safe!")
                    elif risk_score < 0.6:
                        st.warning("⚠️ Medium Risk")
                        st.session_state.vizhibot.display("warning", "Some concerns detected")
                    else:
                        st.error("🚨 High Risk")
                        st.session_state.vizhibot.display("error", "Potential fraud detected!")
                
                with col_status:
                    if risk_score < 0.3:
                        st.success("**Transaction Approved** ✅")
                        st.info("This transaction matches your typical spending patterns.")
                    elif risk_score < 0.6:
                        st.warning("**Review Required** ⚠️")
                        st.info("Please verify this transaction before proceeding.")
                    else:
                        st.error("**Transaction Blocked** 🚫")
                        st.error("Contact security: 1-800-732-8732")
                        add_alert("Fraud Alert", f"High-risk transaction blocked: ₹{amount:,.0f} at {merchant}")
                
                if risk_factors:
                    st.markdown("### 🔬 Risk Factor Breakdown")
                    
                    for factor, score, explanation in risk_factors:
                        col_factor, col_score = st.columns([3, 1])
                        with col_factor:
                            st.markdown(f"**{factor}**")
                            st.caption(explanation)
                        with col_score:
                            risk_class = "risk-high" if score > 0.6 else "risk-medium" if score > 0.3 else "risk-low"
                            st.markdown(f'<p class="{risk_class}">{score:.0%}</p>', unsafe_allow_html=True)
                
                if groq_client:
                    st.markdown("### 🤖 AI Expert Analysis")
                    transaction_data = {
                        'amount': amount,
                        'hour': hour,
                        'merchant': merchant,
                        'category': category
                    }
                    
                    with st.spinner("Generating expert analysis..."):
                        ai_explanation = get_fraud_explanation(transaction_data, risk_score, risk_factors)
                        if ai_explanation:
                            st.info(ai_explanation)
                        else:
                            st.warning("AI analysis temporarily unavailable")
    
    with tab2:
        st.markdown("### 📊 Spending Pattern Anomaly Detection")
        
        if st.button("🔍 Detect Anomalies", type="primary"):
            recent_transactions, anomalies = detect_spending_anomalies()
            
            if not recent_transactions:
                st.info("Not enough transaction data. Make some payments to enable anomaly detection.")
            else:
                st.success(f"✅ Analyzed {len(recent_transactions)} transactions from the last 30 days")
                
                if anomalies:
                    st.warning(f"⚠️ Found {len(anomalies)} unusual transactions")
                    
                    for anomaly in anomalies:
                        t = anomaly['transaction']
                        with st.expander(f"🚨 Unusual: ₹{t['amount']:,.0f} - {t.get('category', 'N/A')} ({anomaly['deviation']})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Amount:** ₹{t['amount']:,.0f}")
                                st.write(f"**Category:** {t.get('category', 'N/A')}")
                                st.write(f"**Time:** {t['hour']}:00")
                            with col2:
                                st.write(f"**Date:** {t['timestamp'].strftime('%Y-%m-%d')}")
                                st.write(f"**Z-Score:** {anomaly['z_score']:.2f}")
                                st.metric("Deviation", anomaly['deviation'])
                else:
                    st.success("✅ No anomalies detected. All transactions look normal!")
                
                if len(recent_transactions) >= 5:
                    st.markdown("### 📈 Spending Trend")
                    amounts = [t['amount'] for t in recent_transactions]
                    dates = [t['timestamp'] for t in recent_transactions]
                    
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(dates, amounts, marker='o', linestyle='-', linewidth=2, markersize=6)
                    ax.axhline(y=np.mean(amounts), color='g', linestyle='--', label='Average')
                    ax.axhline(y=np.mean(amounts) + 2*np.std(amounts), color='r', linestyle='--', label='Anomaly Threshold')
                    ax.set_xlabel('Date')
                    ax.set_ylabel('Amount (₹)')
                    ax.set_title('Transaction Amount Over Time')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
    
    with tab3:
        st.markdown("### 🛡️ Security Dashboard")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Alerts", len(st.session_state.alerts))
            st.metric("Blocked Transactions", "3")
        
        with col2:
            st.metric("Risk Score", "Low", delta="-15%")
            st.metric("Suspicious Activities", "0")
        
        with col3:
            st.metric("Account Status", "✅ Secure")
            st.metric("Last Security Scan", "2 mins ago")
        
        st.markdown("---")
        st.markdown("### 🔒 Security Recommendations")
        
        recommendations = [
            ("Enable Two-Factor Authentication", "🔐", "success"),
            ("Review Recent Transactions", "📝", "info"),
            ("Update Security Questions", "❓", "warning"),
            ("Monitor Credit Score", "📊", "info")
        ]
        
        for rec, icon, status in recommendations:
            col_icon, col_text = st.columns([1, 10])
            with col_icon:
                st.markdown(f"### {icon}")
            with col_text:
                if status == "success":
                    st.success(f"✅ {rec}")
                elif status == "warning":
                    st.warning(f"⚠️ {rec}")
                else:
                    st.info(f"ℹ️ {rec}")

# --- MODULE 3: Make Payment ---
elif app_mode == "💳 Make Payment":
    st.session_state.vizhibot.display("money", "Ready to process your payment")
    
    st.subheader("💳 Secure Payment Processing")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Payment Details")
        
        recipient = st.text_input("Recipient Name", placeholder="John Doe")
        amount = st.number_input("Amount (₹)", min_value=0.0, value=1000.0, step=100.0)
        merchant = st.text_input("Merchant/Description", value="Amazon India")
        category = st.selectbox("Category", ["Online Shopping", "Restaurant", "Groceries", "Electronics", 
                                             "Entertainment", "Transport", "Healthcare", "Bill Payment", "Other"])
        
        payment_method = st.radio("Payment Method", ["UPI", "Credit Card", "Debit Card", "Net Banking"])
        
        current_hour = datetime.now().hour
        hour = st.slider("Transaction Time (Hour)", 0, 23, current_hour)
        
        st.info(f"💡 Processing payment of ₹{amount:,.0f} at {hour}:00")
        
        if st.button("🔒 Process Payment", type="primary", use_container_width=True):
            st.session_state.vizhibot.display("processing", "Analyzing payment security...")
            
            with st.spinner("Running security checks..."):
                time.sleep(1.5)
                
                risk_score, risk_factors = predict_payment_risk(amount, category, hour, merchant)
                
                st.markdown("---")
                st.markdown("### 🔍 Security Analysis")
                
                col_risk, col_decision = st.columns([1, 2])
                
                with col_risk:
                    st.metric("Risk Score", f"{risk_score:.0%}")
                    
                    if risk_score < 0.3:
                        st.success("✅ Low Risk")
                    elif risk_score < 0.6:
                        st.warning("⚠️ Medium Risk")
                    else:
                        st.error("🚨 High Risk")
                
                with col_decision:
                    if risk_score < 0.3:
                        st.success("### ✅ Payment Approved")
                        st.balloons()
                        st.session_state.vizhibot.display("celebrate", "Payment successful!")
                        
                        st.session_state.spending_profile.learn_from_transaction(amount, category, hour)
                        
                        st.session_state.transaction_history.append({
                            'amount': amount,
                            'merchant': merchant,
                            'category': category,
                            'hour': hour,
                            'timestamp': datetime.now(),
                            'status': 'Approved',
                            'risk_score': risk_score
                        })
                        
                        st.info(f"💳 ₹{amount:,.0f} sent to {recipient}")
                        st.caption("Transaction ID: TXN" + str(random.randint(100000, 999999)))
                        
                    elif risk_score < 0.6:
                        st.warning("### ⚠️ Additional Verification Required")
                        st.session_state.vizhibot.display("warning", "Please verify your identity")
                        st.info("📱 We've sent an OTP to your registered mobile number")
                        
                        otp = st.text_input("Enter OTP", max_chars=6)
                        if st.button("Verify & Process"):
                            st.success("✅ Payment approved after verification")
                            st.session_state.spending_profile.learn_from_transaction(amount, category, hour)
                    
                    else:
                        st.error("### 🚫 Payment Blocked")
                        st.session_state.vizhibot.display("error", "Transaction blocked for security")
                        st.error("This transaction has been blocked due to high fraud risk.")
                        st.warning("📞 Contact Security: 1-800-732-8732")
                        
                        add_alert("Fraud Alert", f"Blocked payment of ₹{amount:,.0f} to {merchant}")
                
                if risk_factors:
                    with st.expander("📊 View Detailed Risk Analysis"):
                        for factor, score, explanation in risk_factors:
                            col_f, col_s = st.columns([3, 1])
                            with col_f:
                                st.markdown(f"**{factor}**")
                                st.caption(explanation)
                            with col_s:
                                risk_class = "risk-high" if score > 0.6 else "risk-medium" if score > 0.3 else "risk-low"
                                st.markdown(f'<p class="{risk_class}">{score:.0%}</p>', unsafe_allow_html=True)
                
                if groq_client and risk_score >= 0.3:
                    st.markdown("### 🤖 AI Risk Assessment")
                    transaction_data = {
                        'amount': amount,
                        'hour': hour,
                        'merchant': merchant,
                        'category': category
                    }
                    
                    with st.spinner("Generating risk assessment..."):
                        ai_explanation = get_fraud_explanation(transaction_data, risk_score, risk_factors)
                        if ai_explanation:
                            st.info(ai_explanation)
    
    with col2:
        st.markdown("### 💰 Quick Amounts")
        
        quick_amounts = [500, 1000, 2000, 5000, 10000]
        for amt in quick_amounts:
            if st.button(f"₹{amt:,}", use_container_width=True, key=f"quick_{amt}"):
                st.session_state.quick_amount = amt
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Spending Summary")
        st.metric("This Week", f"₹{st.session_state.spending_profile.weekly_spending:,.0f}")
        st.metric("This Month", "₹45,230")
        st.metric("Remaining Budget", "₹4,770")

# --- MODULE 4: Account Dashboard ---
elif app_mode == "📊 Account Dashboard":
    st.session_state.vizhibot.display("analyzing", "Analyzing your financial data...")
    
    st.subheader("📊 Account Dashboard & Insights")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Account Balance", "₹82,450", delta="↑ ₹5,200")
    
    with col2:
        st.metric("Monthly Spending", "₹45,230", delta="↓ ₹3,100")
    
    with col3:
        st.metric("Total Assets", "₹3,45,320", delta="↑ ₹12,500")
    
    with col4:
        st.metric("Credit Score", "780", delta="↑ 15")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📈 Spending Analysis", "💡 AI Insights", "📜 Transaction History"])
    
    with tab1:
        st.markdown("### 📈 Spending Pattern Analysis")
        
        if st.session_state.spending_profile.transaction_history:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("#### Spending by Category")
                
                categories = {}
                for t in st.session_state.spending_profile.transaction_history[-30:]:
                    cat = t.get('category', 'Other')
                    categories[cat] = categories.get(cat, 0) + t['amount']
                
                if categories:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    cats = list(categories.keys())
                    amounts = list(categories.values())
                    colors = plt.cm.Set3(range(len(cats)))
                    
                    ax.pie(amounts, labels=cats, autopct='%1.1f%%', colors=colors, startangle=90)
                    ax.axis('equal')
                    plt.title('Spending Distribution by Category')
                    st.pyplot(fig)
            
            with col2:
                st.markdown("#### Top Categories")
                sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
                for i, (cat, amt) in enumerate(sorted_cats[:5], 1):
                    st.metric(f"{i}. {cat}", f"₹{amt:,.0f}")
            
            st.markdown("#### Spending by Time of Day")
            time_data = {'Morning': 0, 'Afternoon': 0, 'Evening': 0, 'Night': 0}
            for t in st.session_state.spending_profile.transaction_history[-30:]:
                hour = t['hour']
                if 5 <= hour < 12:
                    time_data['Morning'] += t['amount']
                elif 12 <= hour < 17:
                    time_data['Afternoon'] += t['amount']
                elif 17 <= hour < 22:
                    time_data['Evening'] += t['amount']
                else:
                    time_data['Night'] += t['amount']
            
            fig, ax = plt.subplots(figsize=(10, 4))
            times = list(time_data.keys())
            amounts = list(time_data.values())
            bars = ax.bar(times, amounts, color=['#FFD700', '#FF6347', '#4169E1', '#9370DB'])
            ax.set_xlabel('Time of Day')
            ax.set_ylabel('Amount (₹)')
            ax.set_title('Spending Pattern by Time')
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'₹{height:,.0f}',
                       ha='center', va='bottom')
            
            st.pyplot(fig)
        else:
            st.info("No transaction data available yet. Make some payments to see insights!")
    
    with tab2:
        st.markdown("### 💡 AI-Powered Financial Insights")
        
        if st.button("🤖 Generate Insights", type="primary"):
            if groq_client:
                st.session_state.vizhibot.display("thinking", "Analyzing your spending patterns...")
                
                with st.spinner("Generating personalized insights..."):
                    insights = get_spending_insights(st.session_state.spending_profile)
                    
                    if insights:
                        st.success("### Your Personalized Insights")
                        st.markdown(insights)
                        
                        st.markdown("---")
                        st.markdown("### 📌 Action Items")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info("✅ Set up automatic savings")
                            st.info("📊 Review monthly budget")
                        with col2:
                            st.info("🔔 Enable spending alerts")
                            st.info("💰 Optimize subscriptions")
                    else:
                        st.warning("Unable to generate insights at this time.")
            else:
                st.warning("⚠️ AI insights require Groq API key. Please configure GROQ_API_KEY.")
        
        st.markdown("---")
        st.markdown("### 🎯 Financial Goals")
        
        col1, col2 = st.columns(2)
        with col1:
            st.progress(0.65)
            st.caption("Emergency Fund: 65% (₹65,000 / ₹1,00,000)")
        with col2:
            st.progress(0.40)
            st.caption("Vacation Savings: 40% (₹20,000 / ₹50,000)")
    
    with tab3:
        st.markdown("### 📜 Recent Transaction History")
        
        if st.session_state.transaction_history:
            for i, txn in enumerate(reversed(st.session_state.transaction_history[-10:])):
                with st.expander(f"💳 ₹{txn['amount']:,.0f} - {txn['merchant']} ({txn['status']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Amount:** ₹{txn['amount']:,.0f}")
                        st.write(f"**Merchant:** {txn['merchant']}")
                        st.write(f"**Category:** {txn['category']}")
                    with col2:
                        st.write(f"**Time:** {txn['hour']}:00")
                        st.write(f"**Date:** {txn['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Status:** {txn['status']}")
                        st.metric("Risk Score", f"{txn['risk_score']:.0%}")
        else:
            st.info("No payment transactions yet. Use the 'Make Payment' module to process payments.")
        
        st.markdown("---")
        
        if st.session_state.spending_profile.transaction_history:
            st.markdown("### 📊 All Transactions (Last 30 Days)")
            
            recent = st.session_state.spending_profile.transaction_history[-30:]
            df = pd.DataFrame(recent)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False)
            
            st.dataframe(
                df[['timestamp', 'amount', 'category', 'hour']],
                use_container_width=True,
                hide_index=True
            )
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Transaction History",
                data=csv,
                file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# --- Footer ---
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🏦 SecureBank")
    st.caption("Your trusted banking partner")

with col2:
    st.markdown("### 📞 Support")
    st.caption("1-800-732-8732")
    st.caption("support@securebank.com")

with col3:
    st.markdown("### 🔒 Security")
    st.caption("256-bit SSL Encryption")
    st.caption("PCI DSS Compliant")
