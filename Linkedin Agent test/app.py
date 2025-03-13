import streamlit as st
from dotenv import load_dotenv
import openai
from datetime import datetime
import emoji
import os
import json
from tavily import TavilyClient
import validators
import re

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Gaurav's LinkedIn Agent",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Initialize Tavily client
tavily = TavilyClient(api_key="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")

# Custom CSS with added comparison styles
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #f3f2ef;
    }
    .stButton>button {
        background-color: #0a66c2;
        color: white;
        border-radius: 24px;
        padding: 10px 20px;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #004182;
    }
    .output-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 10px 0;
    }
    .refinement-box {
        background-color: #f3f2ef;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .source-box {
        background-color: #e8f4f9;
        padding: 10px;
        border-radius: 4px;
        margin: 5px 0;
        font-size: 0.9em;
    }
    .css-1v0mbdj.etr89bj1 {
        margin-top: 20px;
    }
    h1 {
        color: #0a66c2;
    }
    .linkedin-tips {
        background-color: #f3f2ef;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .comparison-container {
        display: flex;
        gap: 20px;
        margin: 20px 0;
    }
    .original-post, .refined-post {
        flex: 1;
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .original-post {
        border-left: 4px solid #0a66c2;
    }
    .refined-post {
        border-left: 4px solid #057642;
    }
    .changes-list {
        background-color: #f0f7ff;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .web-search-result {
        background-color: #f5f5f5;
        padding: 12px;
        border-radius: 6px;
        margin: 8px 0;
        border-left: 3px solid #0a66c2;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session states
if 'post_history' not in st.session_state:
    st.session_state.post_history = []
if 'current_post' not in st.session_state:
    st.session_state.current_post = None
if 'current_sources' not in st.session_state:
    st.session_state.current_sources = []
if 'current_trends' not in st.session_state:
    st.session_state.current_trends = []
if 'original_post' not in st.session_state:
    st.session_state.original_post = None
if 'url_content' not in st.session_state:
    st.session_state.url_content = None

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_regex, url)
    return match.group(1) if match else None

def get_video_details(video_id):
    """Get video details from YouTube API"""
    try:
        # Get video details
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()

        if not video_response['items']:
            return None

        video_data = video_response['items'][0]
        snippet = video_data['snippet']
        statistics = video_data['statistics']

        # Get video comments
        comments = []
        try:
            comments_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=10,
                order='relevance'
            ).execute()

            for item in comments_response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append(comment['textDisplay'])
        except:
            # Comments might be disabled
            pass

        return {
            'title': snippet['title'],
            'description': snippet['description'],
            'channel': snippet['channelTitle'],
            'published_at': snippet['publishedAt'],
            'view_count': statistics.get('viewCount', '0'),
            'like_count': statistics.get('likeCount', '0'),
            'comment_count': statistics.get('commentCount', '0'),
            'comments': comments
        }
    except HttpError as e:
        st.error(f"Error fetching video details: {str(e)}")
        return None

def get_youtube_content(url):
    """Get content from YouTube video using multiple methods"""
    try:
        video_id = extract_youtube_id(url)
        if not video_id:
            st.error("Could not extract YouTube video ID. Please check the URL.")
            return None

        # First, try to get video details from YouTube API
        video_details = get_video_details(video_id)
        if not video_details:
            st.error("Could not fetch video details from YouTube.")
            return None

        # Try to get transcript if available
        transcript_text = ""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = ' '.join([entry['text'] for entry in transcript_list])
        except:
            # If transcript fails, we'll work with video details only
            pass

        # Combine all available content
        content = f"""Video Title: {video_details['title']}
Channel: {video_details['channel']}
Views: {video_details['view_count']}
Likes: {video_details['like_count']}

Description:
{video_details['description']}

{"Transcript:" if transcript_text else ""}
{transcript_text if transcript_text else ""}

{"Top Comments:" if video_details['comments'] else ""}
{chr(10).join(f"- {html.unescape(comment)}" for comment in video_details['comments'][:5]) if video_details['comments'] else ""}
"""

        return {
            'title': video_details['title'],
            'content': content,
            'video_id': video_id,
            'url': url,
            'channel': video_details['channel'],
            'views': video_details['view_count'],
            'likes': video_details['like_count']
        }
    except Exception as e:
        st.error(f"Error processing YouTube video: {str(e)}")
        return None

def is_youtube_url(url):
    """Check if the URL is a YouTube video URL"""
    return False  # YouTube functionality removed

def analyze_url(url):
    """Analyze URL content using Tavily API"""
    try:
        # Use Tavily to analyze the URL with focus on recent content
        result = tavily.search(
            query="latest developments current trends 2024 2025",
            url=url,
            search_depth="advanced",
            include_answer=True,
            max_results=3,
            sort_by="date"
        )
        
        # Extract the content
        if result and 'results' in result and len(result['results']) > 0:
            # Try to find the most recent content
            most_recent = None
            for item in result['results']:
                content = item.get('content', '').lower()
                if '2024' in content or '2025' in content:
                    most_recent = item
                    break
            
            # If no recent content found, use the first result
            if not most_recent:
                most_recent = result['results'][0]
            
            return {
                'title': most_recent.get('title', ''),
                'content': most_recent.get('content', ''),
                'url': url,
                'date': most_recent.get('published_date', 'Recent')
            }
        return None
    except Exception as e:
        st.warning(f"Could not analyze URL: {str(e)}")
        return None

def search_recent_news(query, num_results=5):
    """Search for recent news and trends related to the topic using Azure OpenAI"""
    try:
        client = openai.AzureOpenAI(
            api_key=os.environ.get("AZURE_API_KEY", "d2fc3cb33a1046b5936b9d9995322f2d"),
            api_version="2023-05-15",
            azure_endpoint="https://idpoai.openai.azure.com"
        )
        
        search_prompt = f"""Find {num_results} very recent news articles, developments, or trends about "{query}" from 2024-2025.
        Focus on the most recent developments, predictions, and current state as of 2025.
        For each result, provide:
        1. A title that reflects current 2024-2025 developments
        2. A brief description highlighting the most recent updates
        3. A date from 2024-2025
        
        Format each result as:
        Title: [title]
        Date: [YYYY-MM-DD] (use dates between 2024-2025 only)
        Description: [brief description emphasizing current developments]
        ---"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI that specializes in finding and summarizing the most recent news and trends from 2024-2025. Always focus on the latest developments and current state of affairs."},
                {"role": "user", "content": search_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse the response into structured format
        content = response.choices[0].message.content
        articles = []
        
        # Split the content into individual articles
        raw_articles = content.split("---")
        for article in raw_articles:
            if not article.strip():
                continue
            
            # Extract information using simple parsing
            lines = article.strip().split("\n")
            article_data = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith("Title:"):
                    article_data['title'] = line[6:].strip()
                elif line.startswith("Date:"):
                    article_data['date'] = line[5:].strip()
                elif line.startswith("Description:"):
                    article_data['description'] = line[12:].strip()
            
            if article_data:
                # Ensure date is in 2024-2025 range
                date = article_data.get('date', '')
                if date.startswith(('2024', '2025')):
                    articles.append({
                        'title': article_data.get('title', ''),
                        'description': article_data.get('description', ''),
                        'date': date,
                        'url': ''
                    })
        
        return articles[:num_results]
    except Exception as e:
        st.warning(f"Could not fetch recent news: {str(e)}")
        return []

def generate_linkedin_post(prompt, tone="professional", focus_areas=None, recent_news=None):
    """Generate LinkedIn post using Azure OpenAI"""
    try:
        client = openai.AzureOpenAI(
            api_key=os.environ.get("AZURE_API_KEY", "d2fc3cb33a1046b5936b9d9995322f2d"),
            api_version="2023-05-15",
            azure_endpoint="https://idpoai.openai.azure.com"
        )

        # Include focus areas and recent news in the prompt
        focus_prompt = ""
        if focus_areas:
            focus_prompt = f"Focus on these aspects: {', '.join(focus_areas)}. "
        
        news_prompt = ""
        if recent_news:
            news_prompt = "\nIncorporate these recent developments and trends:\n"
            for news in recent_news:
                news_prompt += f"- {news['title']} ({news['date']})\n"

        system_prompt = f"""You are a professional LinkedIn content creator and thought leader. Create an engaging, data-driven post that demonstrates expertise and sparks meaningful discussions.

        Transform the input into a LinkedIn post with these elements:
        1. 🎯 Strong Hook (First Line):
           - Start with a powerful statistic, question, or statement
           - Use emojis strategically to grab attention
        
        2. 📊 Main Content (2-3 Paragraphs):
           - Include 2-3 recent statistics or data points with sources
           - Break down complex ideas into bullet points
           - Use the {tone} tone throughout
           - Add relevant emojis to key points (1-2 per paragraph)
        
        3. 💡 Value Addition:
           - Share practical insights or actionable takeaways
           - Include industry trends and predictions
           - Reference current developments
        
        4. 🤝 Engagement Hook:
           - End with a thought-provoking question
           - Encourage meaningful discussions
           - Call for sharing experiences
        
        5. #️⃣ Hashtags:
           - Add 5-7 relevant, trending hashtags
        
        {focus_prompt}
        {news_prompt}
        
        Format the response as follows:
        [POST]
        The actual post content
        [SOURCES]
        List of sources with URLs
        [TRENDS]
        List of trends referenced
        [CHANGES]
        List of improvements made (if this is a refinement)"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create an engaging LinkedIn post about: {prompt}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        
        # Split content into sections
        sections = content.split("[")
        post_content = ""
        sources = []
        trends = []
        changes = []
        
        for section in sections:
            if section.startswith("POST]"):
                post_content = section[5:].strip()
            elif section.startswith("SOURCES]"):
                sources = [s.strip() for s in section[8:].strip().split("\n") if s.strip()]
            elif section.startswith("TRENDS]"):
                trends = [t.strip() for t in section[7:].strip().split("\n") if t.strip()]
            elif section.startswith("CHANGES]"):
                changes = [c.strip() for c in section[8:].strip().split("\n") if c.strip()]
        
        # Store the original post if this is not a refinement
        if not focus_areas and not recent_news:
            st.session_state.original_post = post_content
        
        return post_content, sources, trends, changes
    except Exception as e:
        return f"Error generating post: {str(e)}", [], [], []

def tavily_search(query, max_results=5):
    """Perform web search using Tavily API"""
    try:
        # Add time-based context to the query
        current_year = datetime.now().year
        time_aware_query = f"{query} {current_year} breaking news latest developments"
        
        # Perform the search with Tavily
        search_result = tavily.search(
            query=time_aware_query,
            search_depth="advanced",
            max_results=max_results * 2,  # Request more results to filter
            sort_by="date",  # Sort by date to get newest first
            search_type="news",  # Specifically search for news
            include_domains=[
                "timesofindia.indiatimes.com",
                "ndtv.com",
                "indianexpress.com",
                "hindustantimes.com",
                "news18.com",
                "thehindu.com",
                "reuters.com",
                "bloomberg.com"
            ]
        )
        
        # Format and filter the results
        formatted_results = []
        for result in search_result.get('results', []):
            # Try to extract date information
            published_date = result.get('published_date', '')
            if not published_date:
                # Try to find date in content
                content = result.get('content', '').lower()
                title = result.get('title', '').lower()
                date_match = re.search(r'\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+202[4-5]\b', 
                                     content + ' ' + title, 
                                     re.IGNORECASE)
                if date_match:
                    published_date = date_match.group(0)
            
            formatted_results.append({
                'title': result['title'],
                'description': result['content'],
                'url': result['url'],
                'date': published_date or 'Recent'
            })
        
        # Sort by date (newest first) and return the requested number of results
        formatted_results.sort(key=lambda x: x['date'] if x['date'] != 'Recent' else '', reverse=True)
        return formatted_results[:max_results]
    except Exception as e:
        st.warning(f"Could not perform web search: {str(e)}")
        return []

def clean_url(url):
    """Clean and validate URL"""
    url = url.strip()
    if url.startswith("@"):
        url = url[1:]
    return url

def extract_url_content(url):
    """Extract content from URL using appropriate method"""
    try:
        # Clean the URL first
        url = clean_url(url)
        
        # Use Azure OpenAI to analyze the content
        client = openai.AzureOpenAI(
            api_key=os.environ.get("AZURE_API_KEY", "d2fc3cb33a1046b5936b9d9995322f2d"),
            api_version="2023-05-15",
            azure_endpoint="https://idpoai.openai.azure.com"
        )
        
        system_prompt = """You are an expert content analyzer. Extract and summarize the main content from the given URL.
        Provide the response in the following format:
        [TITLE]
        The main title or topic
        [CONTENT]
        A detailed summary of the content (400-500 words)
        [KEY_POINTS]
        - Key point 1
        - Key point 2
        - Key point 3
        - Key point 4
        - Key point 5"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze and extract content from this URL: {url}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        sections = content.split("[")
        
        return {
            'title': sections[1].split("]")[1].strip() if len(sections) > 1 else "",
            'content': sections[2].split("]")[1].strip() if len(sections) > 2 else "",
            'key_points': [p.strip() for p in sections[3].split("]")[1].strip().split("\n") if p.strip()] if len(sections) > 3 else [],
            'url': url,
            'is_video': False
        }
    except Exception as e:
        st.warning(f"Could not analyze URL: {str(e)}")
        return None

# Sidebar content
with st.sidebar:
    st.image("https://content.linkedin.com/content/dam/me/business/en-us/amp/brand-site/v2/bg/LI-Logo.svg.original.svg", width=200)
    st.markdown("### Writing Tips 📝")
    st.markdown("""
    1. **Be Specific** in your topic
    2. **Include Data** - Back claims with statistics
    3. **Source Everything** - Add credibility with links
    4. **Current Trends** - Reference ongoing discussions
    5. **Call to Action** - End with engagement prompt
    """)
    
    st.markdown("---")
    
    if st.session_state.post_history:
        st.markdown("### Recent Posts")
        for i, post in enumerate(reversed(st.session_state.post_history[-3:])):
            st.markdown(f"**{post['timestamp']}**")
            st.markdown(f"_{post['prompt']}_")
            st.markdown("---")

# Main content area
st.title("🚀 Gaurav's LinkedIn Agent")

# Input Tabs
input_type = st.radio("Choose Input Type:", ["✍️ Write Topic", "🔗 Use URL"], horizontal=True)

if input_type == "✍️ Write Topic":
    # Existing topic input section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 1️⃣ Enter Your Topic")
        user_prompt = st.text_area("What would you like to create a post about?", height=100)
else:
    # URL input section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 1️⃣ Enter URL")
        url_input = st.text_input("Paste a URL (webpage, LinkedIn post, etc.)")
        
        if url_input:
            cleaned_url = clean_url(url_input)
            if not validators.url(cleaned_url):
                st.error("Please enter a valid URL")
            else:
                with st.spinner("🔍 Analyzing URL content..."):
                    url_content = extract_url_content(cleaned_url)
                    if url_content:
                        st.session_state.url_content = url_content
                        st.success("URL analyzed successfully!")
                        with st.expander("View extracted content", expanded=True):
                            st.markdown(f"**Title:** {url_content['title']}")
                            
                            if url_content.get('is_video', False):
                                st.video(f"https://www.youtube.com/watch?v={url_content['video_id']}")
                            
                            st.markdown("**Content Summary:**")
                            st.markdown(url_content['content'])
                            if url_content['key_points']:
                                st.markdown("**Key Points:**")
                                for point in url_content['key_points']:
                                    st.markdown(f"• {point}")
                        
                        # Create a comprehensive prompt from the extracted content
                        user_prompt = f"""Create an engaging LinkedIn post based on this content:

Title: {url_content['title']}

Key Points:
{chr(10).join('- ' + point for point in url_content['key_points'])}

Detailed Content:
{url_content['content']}

Source: {url_content['url']}

Make sure to:
1. Highlight key insights and findings
2. Include specific implications
3. Discuss future outlook and potential impact
4. Add relevant hashtags"""
                    else:
                        st.error("Could not analyze the URL. Please try a different URL or enter your topic directly.")
                        user_prompt = ""
    
with col2:
    st.markdown("### ⚙️ Post Settings")
    tone = st.selectbox("Tone:", 
        ["professional", "conversational", "technical", "inspirational", "analytical"],
        label_visibility="collapsed")
    
    focus_options = [
        "Industry Trends", "Data & Statistics", "Professional Growth",
        "Innovation", "Leadership", "Technology", "Best Practices",
        "Future Predictions", "Case Studies"
    ]
    selected_focus = st.multiselect("Focus Areas:", focus_options, label_visibility="collapsed")

if st.button("Generate Post", type="primary"):
    if user_prompt:
        # Only do web search if using topic input, not URL
        if input_type == "✍️ Write Topic":
            with st.spinner("🔎 Searching the web for latest information..."):
                web_results = tavily_search(user_prompt)
                
                if web_results:
                    st.markdown("### 🌐 Latest Web Search Results")
                    cols = st.columns(2)
                    for idx, result in enumerate(web_results, 1):
                        with cols[idx % 2].expander(f"Result {idx}: {result['title']}", expanded=idx == 1):
                            st.markdown(f"**Source:** [{result['url']}]({result['url']})")
                            st.markdown(f"**Content:** {result['description']}")
                            st.markdown(f"**Date:** {result['date']}")
        else:
            web_results = []  # No web search for URL input
            
        with st.spinner("✍️ Generating your LinkedIn post..."):
            # Generate the post using web results for topics, or URL content for URLs
            post_content, sources, trends, changes = generate_linkedin_post(
                prompt=user_prompt,
                tone=tone,
                focus_areas=selected_focus,
                recent_news=web_results
            )
            
            # Store the generated post in session state
            st.session_state.current_post = post_content
        st.session_state.current_sources = sources
        st.session_state.current_trends = trends
        
# Create two columns for the main content and refinement options
main_col, refine_col = st.columns([2, 1])

with main_col:
    if st.session_state.current_post:
        st.markdown("### 📝 Generated LinkedIn Post")
        st.markdown('<div class="output-box">' + st.session_state.current_post + '</div>', unsafe_allow_html=True)
        
        if st.session_state.current_sources:
            st.markdown("### 📚 Sources Used")
            for source in st.session_state.current_sources:
                st.markdown(f"- {source}")
        
        if st.session_state.current_trends:
            st.markdown("### 📈 Current Trends")
            for trend in st.session_state.current_trends:
                st.markdown(f"- {trend}")

with refine_col:
    if st.session_state.current_post:
        st.markdown("### ✨ Refine Your Post")
        refinement_options = st.multiselect(
            "Improve aspects:",
            ["More Statistics", "More Current Trends", "Shorter Paragraphs", 
             "More Professional Tone", "More Emojis", "More Technical Details", 
             "More Case Studies"],
            label_visibility="collapsed"
        )
        
        refine_prompt = st.text_area(
            "Additional instructions:",
            placeholder="e.g., Add more specific examples...",
            label_visibility="collapsed"
        )
        
        if st.button("Refine Post ✨", use_container_width=True) and (refinement_options or refine_prompt):
            with st.spinner("🔄 Refining..."):
                # Get fresh web search results for refinement
                web_results = tavily_search(user_prompt)
                
                refinement_focus = refinement_options + ([refine_prompt] if refine_prompt else [])
                refined_post, new_sources, new_trends, changes = generate_linkedin_post(
                    user_prompt, 
                    tone, 
                    refinement_focus,
                    web_results
                )
                
                st.markdown("### 📝 Refined Version")
                st.markdown('<div class="refined-post">' + refined_post + '</div>', unsafe_allow_html=True)
                
                if changes:
                    with st.expander("🔄 View Changes"):
                        for change in changes:
                            st.markdown(f"• {change}")
                
                if new_sources:
                    with st.expander("📚 New Sources"):
                        for source in new_sources:
                            st.markdown(f"- {source}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("📋 Copy", 
                     help="Copy refined post",
                     on_click=lambda: st.write(st.text_area("", value=refined_post)),
                     use_container_width=True)
        with col2:
            st.button("🔄 Retry", 
                     on_click=lambda: generate_linkedin_post(user_prompt, tone, refinement_focus, web_results),
                     use_container_width=True)
    else:
        st.info("Generate a post first to see refinement options.") 