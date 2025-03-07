import streamlit as st
import openai
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Initialize API keys
AZURE_API_KEY = os.getenv("AZURE_API_KEY", "d2fc3cb33a1046b5936b9d9995322f2d")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://idpoai.openai.azure.com")

# Configure OpenAI
openai.api_type = "azure"
openai.api_key = AZURE_API_KEY
openai.api_base = AZURE_ENDPOINT
openai.api_version = "2023-05-15"

# Page configuration
st.set_page_config(
    page_title="LinkedIn Post Generator",
    page_icon="📝",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stButton>button {
        background-color: #0a66c2;
        color: white;
        border-radius: 24px;
        padding: 10px 20px;
        font-weight: 600;
        width: 100%;
    }
    .stTextArea>div>div>textarea {
        background-color: #f3f6f9;
    }
    </style>
    """, unsafe_allow_html=True)

def generate_linkedin_post(prompt, tone="professional"):
    """Generate LinkedIn post using Azure OpenAI"""
    try:
        system_prompt = f"""You are a professional LinkedIn content creator. 
        Create an engaging post with the following tone: {tone}
        Include:
        - 3-4 concise paragraphs
        - Engaging opening hook
        - Professional insights
        - Call to action
        - 3-5 relevant hashtags
        Make it engaging while maintaining professionalism."""

        response = openai.Completion.create(
            engine="gpt-4",
            prompt=f"System: {system_prompt}\n\nUser: Create a LinkedIn post about: {prompt}",
            temperature=0.7,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error generating post: {str(e)}"

# Main content area
st.title("🚀 LinkedIn Post Generator")
st.markdown("### Transform Your Ideas into Engaging LinkedIn Content")

# Input section with columns
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Enter Your Topic")
    user_prompt = st.text_area(
        "What would you like to create a post about?",
        height=150,
        placeholder="Enter your topic, idea, or key points here..."
    )

with col2:
    st.markdown("### Customize Your Post")
    tone = st.selectbox(
        "Select Tone:",
        ["Professional", "Conversational", "Technical", "Inspirational", "Analytical"],
        index=0
    )

# Generate button
if st.button("Generate Post ✨", use_container_width=True):
    if user_prompt:
        with st.spinner("✍️ Crafting your LinkedIn post..."):
            post_content = generate_linkedin_post(user_prompt, tone.lower())
            st.markdown("### 📝 Your Generated LinkedIn Post")
            st.markdown(post_content)
            
            # Copy button
            st.markdown("---")
            st.markdown("Copy your post and share it on LinkedIn!")
    else:
        st.warning("Please enter a topic for your LinkedIn post.") 