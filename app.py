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
from openai import OpenAI
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

# --- Initialize OpenAI ---
@st.cache_resource
def initialize_openai():
    """Initialize OpenAI client with API key"""
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        st.error(f"Failed to initialize OpenAI: {str(e)}")
        return None

openai_client = initialize_openai()

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
            'morning': {'amount': 1500, 'count': 0},  # In rupees
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
        
        # Update time patterns
        time_period = self._get_time_period(hour)
        self.typical_spending[time_period]['amount'] = (
            self.typical_spending[time_period]['amount'] + amount
        ) / 2
        self.typical_spending[time_period]['count'] += 1
        
        # Update category patterns
        if category not in self.category_patterns:
            self.category_patterns[category] = {'total': 0, 'count': 0}
        self.category_patterns[category]['total'] += amount
        self.category_patterns[category]['count'] += 1
        
        # Update weekly spending (last 7 days only)
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
        
        # 1. Time pattern risk
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
        
        # 2. Category risk
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
        
        # 3. Weekly budget risk
        if self.weekly_spending + amount > 50000:  # Weekly limit in rupees
            overspend_ratio = (self.weekly_spending + amount) / 50000
            risk_score = min(0.5 + (overspend_ratio - 1) * 0.5, 0.9)
            risks.append(risk_score)
            risk_factors.append((
                f"Exceeds weekly spending pattern ({overspend_ratio:.1f}x limit)", 
                risk_score
            ))
        
        # Calculate overall risk score
        if not risks:
            return 0.1, ["Normal spending pattern"], []
        
        # Use maximum risk with weighted average
        max_risk = max(risks) if risks else 0
        avg_risk = sum(risks) / len(risks) if risks else 0
        total_risk = max_risk * 0.7 + avg_risk * 0.3
        
        return min(total_risk, 0.95), risk_factors

# Initialize user spending profile
if "spending_profile" not in st.session_state:
    st.session_state.spending_profile = SpendingProfile()
    # Pre-train with some typical spending
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
    
    # Show OpenAI status
    if openai_client:
        st.success("🤖 AI Enhanced Mode")
    else:
        st.info("🔧 Standard Mode")
    
    # Alert notifications
    if st.session_state.alerts:
        st.divider()
        st.header("🔔 Alerts")
        for i, alert in enumerate(st.session_state.alerts[-3:]):  # Show last 3 alerts
            st.warning(f"{alert['type']}: {alert['message']}")
            if st.button(f"Dismiss", key=f"dismiss_{i}"):
                st.session_state.alerts.pop(i)
                st.rerun()

# --- Load AI Models ---
@st.cache_resource
def load_models():
    # Load QA Model
    try:
        qa_model = pipeline("question-answering")
    except:
        qa_model = None
    
    # Load Fraud Model
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

# --- OpenAI Integration Functions ---
def get_openai_response(user_query, conversation_history=None):
    """
    Get intelligent response from OpenAI GPT with banking context
    Falls back to original QA model if OpenAI unavailable
    """
    if not openai_client:
        # Fallback to original transformers model
        if qa_model:
            try:
                result = qa_model(question=user_query, context=banking_context)
                return result['answer'] if result['score'] > 0.2 else "I'm not sure about that. Please contact our support team."
            except:
                return "I'm having trouble connecting to the knowledge base."
        return "AI service temporarily unavailable. Please contact support."
    
    try:
        # Build conversation context
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
        
        # Add conversation history if provided
        if conversation_history:
            for speaker, message in conversation_history[-6:]:  # Last 3 exchanges
                role = "user" if speaker == "user" else "assistant"
                messages.append({"role": role, "content": message})
        
        # Add current query
        messages.append({"role": "user", "content": user_query})
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use gpt-4-turbo-preview for better responses
            messages=messages,
            temperature=0.7,
            max_tokens=300,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Fallback to original model
        if qa_model:
            try:
                result = qa_model(question=user_query, context=banking_context)
                return result['answer'] if result['score'] > 0.2 else "I'm having trouble right now. Please try again."
            except:
                pass
        return "I'm experiencing technical difficulties. Please contact our support team."

def get_fraud_explanation(transaction_data, risk_score, risk_factors):
    """
    Get natural language explanation of fraud analysis using OpenAI
    """
    if not openai_client:
        return None
    
    try:
        prompt = f"""As a fraud detection expert, explain this transaction analysis to a customer:

Transaction Details:
- Amount: ₹{transaction_data['amount']:,.2f}
- Time: {transaction_data['hour']}:00
- Merchant: {transaction_data['merchant']}
- Risk Score: {risk_score:.0%}

Risk Factors Detected:
{chr(10).join([f"- {factor}: {score:.0%} ({explanation})" for factor, score, explanation in risk_factors])}

Provide:
1. Clear summary of the risk level (2-3 sentences)
2. Main concerns identified
3. Recommended action for the customer

Keep it under 100 words, customer-friendly, and actionable."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a fraud prevention expert explaining risks clearly to customers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return None

def get_spending_insights(spending_profile):
    """
    Generate personalized spending insights using OpenAI
    """
    if not openai_client or not spending_profile.transaction_history:
        return None
    
    try:
        # Prepare spending data
        total_spent = sum(t['amount'] for t in spending_profile.transaction_history[-30:])
        categories = {}
        for t in spending_profile.transaction_history[-30:]:
            cat = t.get('category', 'Other')
            categories[cat] = categories.get(cat, 0) + t['amount']
        
        prompt = f"""Analyze this customer's spending and provide 3 personalized insights:

30-Day Spending Summary:
- Total: ₹{total_spent:,.2f}
- Weekly Average: ₹{spending_profile.weekly_spending:,.2f}
- Transactions: {len(spending_profile.transaction_history[-30:])}

Category Breakdown:
{chr(10).join([f"- {cat}: ₹{amt:,.2f}" for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True)])}

Provide:
1. One positive observation
2. One area for potential savings
3. One security or budget tip

Keep each insight to 1 sentence. Be encouraging and practical."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly financial advisor providing helpful spending insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return None

# --- Vizhibot Introduction and Capabilities ---
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
    
    # 1. Check against known fraudulent merchants
    if merchant in FRAUDULENT_MERCHANTS:
        merchant_risk = FRAUDULENT_MERCHANTS[merchant]["risk_score"]
        risk_factors.append((
            f"Known risky merchant ({merchant})", 
            merchant_risk,
            f"This merchant has {FRAUDULENT_MERCHANTS[merchant]['reports']} fraud reports"
        ))
        total_risk = max(total_risk, merchant_risk)
    
    # 2. ML model prediction
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
    
    # 3. Rule-based checks
    if amount > 15000:  # High amount threshold in rupees
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
    
    # Calculate combined risk (weighted towards highest risk factor)
    if risk_factors:
        # Use maximum risk with contribution from other factors
        sorted_factors = sorted(risk_factors, key=lambda x: x[1], reverse=True)
        total_risk = sorted_factors[0][1] * 0.7
        if len(sorted_factors) > 1:
            total_risk += sum(f[1] for f in sorted_factors[1:]) / len(sorted_factors[1:]) * 0.3
        
        total_risk = min(total_risk, 0.95)
    
    return total_risk, risk_factors

# --- Unique Feature 2: Predictive Risk Engine ---
def predict_payment_risk(amount, category, hour, merchant):
    """Predict risk before payment is processed"""
    # Get behavioral risk from spending profile
    behavior_risk, behavior_factors = st.session_state.spending_profile.calculate_behavior_risk(amount, category, hour)
    
    # Get fraud model risk
    fraud_risk, fraud_factors = analyze_transaction(amount, hour, merchant)
    
    # Combine all risk factors
    all_factors = []
    
    # Add behavioral factors
    for factor, score in behavior_factors:
        all_factors.append((f"Behavior: {factor}", score * 0.7, "Based on your spending patterns"))
    
    # Add fraud factors
    for factor, score, explanation in fraud_factors:
        all_factors.append((factor, score, explanation))
    
    # Calculate combined risk (weighted average)
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
    
    # Get recent transactions (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_transactions = [
        t for t in st.session_state.spending_profile.transaction_history 
        if t['timestamp'] > thirty_days_ago
    ]
    
    if len(recent_transactions) < 5:
        return [], []  # Not enough data
    
    amounts = [t['amount'] for t in recent_transactions]
    mean = np.mean(amounts)
    std = np.std(amounts)
    
    # Find anomalies (more than 2 standard deviations from mean)
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
    
    # Simulate email/SMS (in a real app, this would call an API)
    if alert_type == "Fraud Alert":
