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
from datetime import datetime

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
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
        margin: 15px 0;
        border-left: 4px solid #0a66c2;
    }
    .content-box {
        padding: 20px;
        background-color: white;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
        margin: 10px 0;
    }
    .content-comparison {
        display: flex;
        gap: 20px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def summarize_content(text, title=""):
    """Summarize content using Azure OpenAI"""
    try:
        messages = [
            {"role": "system", "content": "You are a professional content summarizer. Create a concise summary that captures the main points and key insights."},
            {"role": "user", "content": f"Title: {title}\n\nContent to summarize:\n{text}"}
        ]

        response = openai.ChatCompletion.create(
            engine=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.5,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error summarizing content: {str(e)}")
        return None

def get_web_search_results(topic):
    """Get web search results using Tavily API"""
    try:
        search_result = tavily.search(
            query=topic,
            search_depth="advanced",
            include_domains=["linkedin.com", "medium.com", "forbes.com", "entrepreneur.com", "inc.com"],
            include_answer=True,
            max_results=5
        )
        
        if search_result and 'results' in search_result:
            sources = []
            content = []
            
            # Extract answer if available
            if 'answer' in search_result and search_result['answer']:
                content.append(search_result['answer'])
            
            # Process each result
            for result in search_result['results']:
                sources.append({
                    'title': result.get('title', 'Untitled'),
                    'url': result.get('url', ''),
                    'published_date': result.get('published_date', '')
                })
                content.append(result.get('content', ''))
            
            return {
                'content': "\n\n".join(content),
                'sources': sources
            }
        return None
    except Exception as e:
        st.error(f"Error in web search: {str(e)}")
        return None

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
                'channel': snippet['channelTitle'],
                'published_date': snippet['publishedAt'][:10]
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
                    'channel': video_info['channel'],
                    'published_date': video_info['published_date']
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
    """Get content from URL using requests"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Use Tavily to extract main content
            search_result = tavily.search(query=f"summarize the content from {url}")
            if search_result and 'results' in search_result and len(search_result['results']) > 0:
                result = search_result['results'][0]
                return {
                    'content': result['content'],
                    'title': result.get('title', 'Article'),
                    'url': url,
                    'published_date': result.get('published_date', '')
                }
        st.error("Could not extract content from the URL")
        return None
    except Exception as e:
        st.error(f"Error getting URL content: {str(e)}")
        return None

def display_sources(sources, title="Sources Used"):
    """Display sources in a formatted way"""
    st.markdown(f"### 📚 {title}")
    for source in sources:
        published_date = source.get('published_date', '')
        date_str = f"Published: {published_date}" if published_date else ""
        
        st.markdown(f"""
        <div class="source-info">
            <strong>{source['title']}</strong><br>
            {date_str}<br>
            <a href="{source['url']}" target="_blank">Read More</a>
        </div>
        """, unsafe_allow_html=True)

def generate_linkedin_post(content, tone="professional", content_type="topic", source_info=None):
    """Generate LinkedIn post using Azure OpenAI"""
    try:
        context = ""
        if isinstance(content, dict):
            if 'sources' in content:  # Web search results
                context = f"\n\nBased on the following research:\n{content['content']}"
            elif 'content' in content:  # URL content
                context = f"\n\nBased on the article: '{content['title']}'\n{content['content']}"
            elif 'text' in content:  # YouTube content
                video_info = f"Video: '{content.get('title', 'YouTube video')}' by {content.get('channel', 'Unknown channel')}\n"
                context = f"\n\nBased on the video transcript:\n{video_info}{content['text']}"
        else:
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
input_type = st.radio("Choose Input Type:", ["Topic (Web Research)", "URL", "YouTube Video"])

# Input section with columns
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Enter Your Content")
    if input_type == "Topic (Web Research)":
        user_input = st.text_area(
            "What would you like to create a post about?",
            height=150,
            placeholder="Enter your topic for web research..."
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
        with st.spinner("✍️ Researching and crafting your LinkedIn post..."):
            content = None
            content_type = "topic"
            source_info = None

            # Process input based on type
            if input_type == "Topic (Web Research)":
                search_results = get_web_search_results(user_input)
                if search_results:
                    content = search_results
                    source_info = {
                        'type': 'web_research',
                        'sources': search_results['sources']
                    }
            elif input_type == "YouTube Video":
                if not validators.url(user_input):
                    st.error("Please enter a valid YouTube URL")
                else:
                    video_id = extract_youtube_id(user_input)
                    if video_id:
                        content = get_youtube_transcript(video_id)
                        if content:
                            # Summarize transcript
                            summary = summarize_content(content['text'], content.get('title', ''))
                            if summary:
                                content['text'] = summary
                                content_type = "youtube"
                                source_info = {
                                    'type': 'youtube',
                                    'url': user_input,
                                    'title': content.get('title', 'YouTube Video'),
                                    'channel': content.get('channel', 'Unknown Channel'),
                                    'published_date': content.get('published_date', '')
                                }
                    else:
                        st.error("Invalid YouTube URL")
            else:  # URL
                if not validators.url(user_input):
                    st.error("Please enter a valid URL")
                else:
                    content = get_url_content(user_input)
                    if content:
                        # Summarize content
                        summary = summarize_content(content['content'], content['title'])
                        if summary:
                            content['content'] = summary
                            content_type = "url"
                            source_info = {
                                'type': 'url',
                                'url': content['url'],
                                'title': content['title'],
                                'published_date': content.get('published_date', '')
                            }

            if content:
                # Display source information
                if source_info:
                    if source_info['type'] == 'web_research':
                        display_sources(source_info['sources'], "Research Sources")
                    else:
                        st.markdown("### 📚 Source Information")
                        published_date = source_info.get('published_date', '')
                        date_str = f"Published: {published_date}" if published_date else ""
                        
                        st.markdown(f"""
                        <div class="source-info">
                            <strong>{source_info['title']}</strong><br>
                            {date_str}<br>
                            <a href="{source_info['url']}" target="_blank">View Source</a>
                        </div>
                        """, unsafe_allow_html=True)

                # Generate post
                post_content = generate_linkedin_post(content, tone.lower(), content_type)
                if post_content:
                    st.markdown("### 📝 Generated LinkedIn Post")
                    st.markdown('<div class="content-box">', unsafe_allow_html=True)
                    st.markdown(post_content)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Store in session state
                    if 'posts' not in st.session_state:
                        st.session_state.posts = []
                    
                    st.session_state.posts.append({
                        'content': post_content,
                        'source_info': source_info,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
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
                                    st.markdown("### 📝 Post Comparison")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("#### Original Post")
                                        st.markdown('<div class="content-box">', unsafe_allow_html=True)
                                        st.markdown(post_content)
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    with col2:
                                        st.markdown("#### Refined Post")
                                        st.markdown('<div class="content-box">', unsafe_allow_html=True)
                                        st.markdown(refined_content)
                                        st.markdown('</div>', unsafe_allow_html=True)
                                        
                                    # Store refined version
                                    st.session_state.posts.append({
                                        'content': refined_content,
                                        'source_info': source_info,
                                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        'refinement_options': refinement
                                    })
    else:
        st.warning(f"Please enter a {'topic' if input_type == 'Topic (Web Research)' else 'URL'}.") 