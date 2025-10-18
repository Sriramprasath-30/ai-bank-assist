import streamlit as st
import groq
import os

# DEBUG: Check if environment variable is loaded
st.sidebar.title("Debug Info")
st.sidebar.write("Environment variables:", list(os.environ.keys()))
st.sidebar.write("GROQ_API_KEY exists:", "GROQ_API_KEY" in os.environ)
if "GROQ_API_KEY" in os.environ:
    api_key = os.getenv("GROQ_API_KEY")
    st.sidebar.write("API Key length:", len(api_key) if api_key else 0)
    st.sidebar.write("API Key starts with:", api_key[:4] if api_key else "None")

def main():
    st.title("🏦 AI Bank Assistant")
    
    # Get API key
    api_key = os.getenv("GROQ_API_KEY")
    
    if api_key:
        st.success(f"✅ API Key loaded! Length: {len(api_key)}")
        st.info(f"Key starts with: {api_key[:4]}...")
        
        try:
            client = groq.Client(api_key=api_key)
            st.success("✅ Groq client initialized successfully!")
            
            # Your existing chat code here
            
        except Exception as e:
            st.error(f"❌ Client initialization failed: {e}")
            
    else:
        st.error("❌ GROQ_API_KEY not found in environment")
        st.info("Make sure you've:")
        st.info("1. Set the secret in GitHub Codespaces settings")
        st.info("2. Restarted your Codespace after setting the secret")

if __name__ == "__main__":
    main()
