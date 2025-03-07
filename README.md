# LinkedIn Post Generator

An AI-powered LinkedIn post generator that creates engaging content from topics or URLs (including YouTube videos). Built with Streamlit, Azure OpenAI, and Tavily API.

## Features

- Generate LinkedIn posts from topics or URLs
- Support for YouTube video transcripts
- Web search integration using Tavily API
- Multiple tone options
- Post refinement capabilities
- Beautiful, responsive UI

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd linkedin-post-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
AZURE_API_KEY=your_azure_openai_key
AZURE_ENDPOINT=your_azure_endpoint
TAVILY_API_KEY=your_tavily_key
```

4. Run the app:
```bash
streamlit run app.py
```

## API Keys Required

- Azure OpenAI API key
- Tavily API key

## Usage

1. Choose input type (Topic or URL)
2. Enter your topic or paste a URL (supports web pages and YouTube videos)
3. Select tone and focus areas
4. Click "Generate Post"
5. Refine the generated post if needed

## Deployment

The app is deployed on Streamlit Cloud. Visit [app-url] to use it.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/) 