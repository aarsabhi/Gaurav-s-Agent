# LinkedIn Post Generator

A professional web application that transforms simple ideas into engaging LinkedIn posts using Azure OpenAI.

## Features

- Transform single-sentence inputs into comprehensive LinkedIn posts
- Generate 4-5 paragraphs of engaging content
- Add relevant hashtags automatically
- Include appropriate emoticons
- Professional UI with LinkedIn-inspired design
- One-click copy functionality

## Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Azure OpenAI:
   - You'll need your Azure OpenAI API key
   - Azure OpenAI endpoint URL
   - Make sure you have a deployed model (default: gpt-35-turbo)

## Running the Application

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to `http://localhost:8501`

3. Enter your Azure OpenAI credentials in the sidebar

4. Start generating professional LinkedIn posts!

## Usage

1. Enter your main idea or topic in the text area
2. Click "Generate Post"
3. Review the generated content
4. Use the copy button to copy the post to your clipboard
5. Paste directly to LinkedIn

## Note

Make sure to update the `engine` parameter in the code to match your deployed Azure OpenAI model name if different from "gpt-35-turbo". 