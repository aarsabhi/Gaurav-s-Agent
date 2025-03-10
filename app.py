import streamlit as st
import openai
import os
from dotenv import load_dotenv
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import re
from tavily import TavilyClient
import validators
import time

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
openai.api_version = "2023-07-01-preview"

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
    .source-info {
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 5px;
        margin: 10px 0;
    }
    .previous-content {
        padding: 15px;
        background-color: #f3f6f9;
        border-left: 4px solid #0a66c2;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_video_info(video_id):
    """Get YouTube video title and channel name"""
    try:
        api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key=AIzaSyDz8YY8oFe9YGEYe3_0IzOZrYWnm6wKCyM&part=snippet"
        response = requests.get(api_url)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            snippet = data['items'][0]['snippet']
            return {
                'title': snippet['title'],
                'channel': snippet['channelTitle']
            }
    except Exception:
        pass
    return None

def get_youtube_transcript(video_id):
    """Get YouTube video transcript with retry mechanism"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([item['text'] for item in transcript_list])
            
            # Get video information
            video_info = get_youtube_video_info(video_id)
            if video_info:
                return {
                    'text': transcript_text,
                    'title': video_info['title'],
                    'channel': video_info['channel']
                }
            return {'text': transcript_text}
            
        except Exception as e:
            if "Too Many Requests" in str(e) and attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            
            if "TranscriptsDisabled" in str(e):
                st.error("This video does not have closed captions or transcripts enabled.")
            elif "VideoUnavailable" in str(e):
                st.error("This video is unavailable or private.")
            else:
                st.error(f"Could not get transcript: {str(e)}")
            return None
    
    st.error("Failed to get transcript after multiple attempts. Please try again later.")
    return None

def get_url_content(url):
    """Get content from URL using Tavily API"""
    try:
        search_result = tavily.search(query=f"summarize the content from {url}")
        if search_result and 'results' in search_result and len(search_result['results']) > 0:
            result = search_result['results'][0]
            return {
                'content': result['content'],
                'title': result.get('title', 'Article'),
                'url': url
            }
        st.error("No content found from the URL")
        return None
    except Exception as e:
        st.error(f"Error getting URL content: {str(e)}")
        return None

def generate_linkedin_post(content, tone="professional", content_type="topic", source_info=None):
    """Generate LinkedIn post using Azure OpenAI"""
    try:
        context = ""
        if content_type == "url" and isinstance(content, dict):
            context = f"\n\nBased on the article: '{content['title']}'\nContent: {content['content']}"
        elif content_type == "youtube" and isinstance(content, dict):
            video_info = f"Video: '{content.get('title', 'YouTube video')}' by {content.get('channel', 'Unknown channel')}\n" if 'title' in content else ""
            context = f"\n\nBased on the following video transcript:\n{video_info}{content['text']}"
        elif isinstance(content, str):
            context = content

        messages = [
            {"role": "system", "content": f"""You are a professional LinkedIn content creator. 
            Create an engaging post with the following tone: {tone}
            Include:
            - 3-4 concise paragraphs
            - Engaging opening hook
            - Professional insights
            - Call to action
            - 3-5 relevant hashtags
            Make it engaging while maintaining professionalism."""},
            {"role": "user", "content": f"Create a LinkedIn post about: {context}"}
        ]

        response = openai.ChatCompletion.create(
            engine=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        return response.choices[0].message.content.strip()
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
            source_info = None

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
                                source_info = {
                                    'type': 'youtube',
                                    'url': user_input,
                                    'title': content.get('title', 'YouTube Video'),
                                    'channel': content.get('channel', 'Unknown Channel')
                                }
                        else:
                            st.error("Invalid YouTube URL")
                    else:
                        content = get_url_content(user_input)
                        if content:
                            content_type = "url"
                            source_info = {
                                'type': 'url',
                                'url': content['url'],
                                'title': content['title']
                            }

            if content:
                post_content = generate_linkedin_post(content, tone.lower(), content_type, source_info)
                if post_content:
                    # Display source information if available
                    if source_info:
                        st.markdown("### 📚 Source Information")
                        if source_info['type'] == 'youtube':
                            st.markdown(f"""
                            <div class="source-info">
                                <strong>Source:</strong> YouTube Video<br>
                                <strong>Title:</strong> {source_info['title']}<br>
                                <strong>Channel:</strong> {source_info['channel']}<br>
                                <strong>URL:</strong> <a href="{source_info['url']}" target="_blank">{source_info['url']}</a>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="source-info">
                                <strong>Source:</strong> Web Article<br>
                                <strong>Title:</strong> {source_info['title']}<br>
                                <strong>URL:</strong> <a href="{source_info['url']}" target="_blank">{source_info['url']}</a>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("### 📝 Your Generated LinkedIn Post")
                    st.markdown(post_content)
                    
                    # Store the generated content in session state
                    st.session_state['original_post'] = post_content
                    st.session_state['source_info'] = source_info
                    
                    # Refinement options
                    st.markdown("---")
                    st.markdown("### ✨ Refine Your Post")
                    
                    # Display original post in a collapsible section
                    with st.expander("View Original Post", expanded=False):
                        st.markdown('<div class="previous-content">', unsafe_allow_html=True)
                        st.markdown(st.session_state['original_post'])
                        st.markdown('</div>', unsafe_allow_html=True)
                    
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
                                    
                                    # Show comparison
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("#### Original Post")
                                        st.markdown('<div class="previous-content">', unsafe_allow_html=True)
                                        st.markdown(post_content)
                                    
                                    with col2:
                                        st.markdown("#### Refined Post")
                                        st.markdown(refined_content)
    else:
        st.warning(f"Please enter a {'topic' if input_type == 'Topic' else 'URL'}.") 