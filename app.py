import streamlit as st
import openai
import os
from dotenv import load_dotenv
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import re
from tavily import TavilyClient
import validators

# Load environment variables
load_dotenv()

# Initialize API keys
AZURE_API_KEY = os.getenv("AZURE_API_KEY", "d2fc3cb33a1046b5936b9d9995322f2d")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://idpoai.openai.azure.com")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")

# Initialize Tavily client
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# Configure OpenAI
openai.api_type = "azure"
openai.api_key = AZURE_API_KEY
openai.api_base = AZURE_ENDPOINT
openai.api_version = "2023-05-15"  # Azure OpenAI version

# Azure OpenAI Deployment Name
AZURE_DEPLOYMENT_NAME = "gpt-4o"

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

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    pattern = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_transcript(video_id):
    """Get YouTube video transcript"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript_list])
    except Exception as e:
        st.error(f"Error getting YouTube transcript: {str(e)}")
        return None

def get_url_content(url):
    """Get content from URL using Tavily API"""
    try:
        search_result = tavily.search(query=f"summarize the content from {url}")
        if search_result and 'results' in search_result and len(search_result['results']) > 0:
            return search_result['results'][0]['content']
        st.error("No content found from the URL")
        return None
    except Exception as e:
        st.error(f"Error getting URL content: {str(e)}")
        return None

def generate_linkedin_post(content, tone="professional", content_type="topic"):
    """Generate LinkedIn post using Azure OpenAI"""
    try:
        context = ""
        if content_type == "url":
            context = f"\n\nBased on the following content from the URL:\n{content}"
        elif content_type == "youtube":
            context = f"\n\nBased on the following video transcript:\n{content}"

        system_prompt = f"""You are a professional LinkedIn content creator. 
        Create an engaging post with the following tone: {tone}
        Include:
        - 3-4 concise paragraphs
        - Engaging opening hook
        - Professional insights
        - Call to action
        - 3-5 relevant hashtags
        Make it engaging while maintaining professionalism."""

        prompt = f"System: {system_prompt}\n\nUser: Create a LinkedIn post about: {content}{context}"

        response = openai.Completion.create(
            engine=AZURE_DEPLOYMENT_NAME,  # Using the Azure deployment name
            prompt=prompt,
            temperature=0.7,
            max_tokens=800,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        return response.choices[0].text.strip()
    except Exception as e:
        st.error(f"Error generating post: {str(e)}")
        return None

# Main content area
st.title("🚀 LinkedIn Post Generator")
st.markdown("### Transform Your Ideas into Engaging LinkedIn Content")

# Input type selection
input_type = st.radio("Choose Input Type:", ["Topic", "URL", "YouTube Video"])

# Input section with columns
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Enter Your Content")
    if input_type == "Topic":
        user_input = st.text_area(
            "What would you like to create a post about?",
            height=150,
            placeholder="Enter your topic, idea, or key points here..."
        )
    else:
        user_input = st.text_input(
            "Enter URL:",
            placeholder="Paste your URL here..."
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
    if user_input:
        with st.spinner("✍️ Crafting your LinkedIn post..."):
            content = user_input
            content_type = "topic"

            if input_type in ["URL", "YouTube Video"]:
                if not validators.url(user_input):
                    st.error("Please enter a valid URL")
                else:
                    if input_type == "YouTube Video":
                        video_id = extract_youtube_id(user_input)
                        if video_id:
                            content = get_youtube_transcript(video_id)
                            if content:
                                content_type = "youtube"
                        else:
                            st.error("Invalid YouTube URL")
                    else:
                        content = get_url_content(user_input)
                        if content:
                            content_type = "url"

            if content:
                post_content = generate_linkedin_post(content, tone.lower(), content_type)
                if post_content:
                    st.markdown("### 📝 Your Generated LinkedIn Post")
                    st.markdown(post_content)
                    
                    # Refinement options
                    st.markdown("---")
                    st.markdown("### ✨ Refine Your Post")
                    refinement = st.multiselect(
                        "Select refinement options:",
                        ["Make it shorter", "Make it longer", "Add more hashtags", "Make it more professional", "Add statistics"]
                    )
                    
                    if refinement:
                        if st.button("Refine Post ✨", key="refine_button", use_container_width=True):
                            with st.spinner("🔄 Refining your post..."):
                                refinement_prompt = f"Please refine this LinkedIn post with these adjustments: {', '.join(refinement)}\n\nOriginal post:\n{post_content}"
                                refined_content = generate_linkedin_post(refinement_prompt, tone.lower(), "topic")
                                if refined_content:
                                    st.markdown("### 📝 Your Refined LinkedIn Post")
                                    st.markdown(refined_content)
    else:
        st.warning(f"Please enter a {'topic' if input_type == 'Topic' else 'URL'}.") 