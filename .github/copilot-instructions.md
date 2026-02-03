# VYUD-AI-Scheduler - Copilot Instructions

## Project Overview

This is an AI-powered scheduler for automated posting to Telegram and LinkedIn channels. The application uses Groq AI to generate social media content and posts it to both platforms.

## Tech Stack

- **Python 3.x**
- **Flask** - Web framework for API endpoints
- **Streamlit** - UI framework for web interface
- **Groq API** - AI text generation
- **Telegram Bot API** - Telegram channel posting
- **LinkedIn API** - LinkedIn profile posting
- **SQLite** - Post history database

## Project Structure

- `app.py` - Flask API server for post management
- `streamlit_app.py` - Streamlit web UI
- `auto_post.py` - Main automation script for generating and posting content
- `telegram_poster.py` - Telegram API integration
- `linkedin_poster.py` - LinkedIn API integration
- `requirements.txt` - Python dependencies

## Environment Variables

Required environment variables for this project:

```
TELEGRAM_BOT_TOKEN - Telegram bot token for API access
TELEGRAM_CHAT_ID - Telegram channel/chat ID
LINKEDIN_ACCESS_TOKEN - LinkedIn OAuth access token
LINKEDIN_PROFILE_ID - LinkedIn profile/organization ID
GROQ_API_KEY - Groq API key for AI content generation
```

Always check for these environment variables before implementing features that use external APIs.

## Running the Application

### Flask API Server
```bash
python app.py
```
Runs on http://0.0.0.0:5000

### Streamlit UI
```bash
streamlit run streamlit_app.py
```

### Auto-posting Script
```bash
python auto_post.py
```

## Code Style Guidelines

### General Python
- Use type hints where possible
- Follow PEP 8 style guidelines
- Use meaningful variable names in both English and Russian (project supports bilingual comments)
- Keep functions focused and single-purpose
- Add docstrings to classes and public methods

### Error Handling
- Always use try-except blocks for API calls
- Log errors with appropriate log levels (ERROR, WARNING, INFO)
- Return structured responses with status and message fields
- Use timeout parameters for all HTTP requests (default: 10 seconds)

### Logging
- Use Python's `logging` module
- Configure logging at the module level: `logger = logging.getLogger(__name__)`
- Log format: `'%(asctime)s - %(levelname)s - %(message)s'`
- Log all API interactions (successful and failed)

### API Integrations
- Each platform (Telegram, LinkedIn) has its own class
- Classes should initialize with environment variables
- Implement `post_text()` method for posting content
- Return consistent response format: `{"status": "success/error", "message": "...", "data": {...}}`
- Always validate credentials before making API calls

### Database
- SQLite database file: `posts.db`
- Table: `post_history` with fields: id, platform, content, status, timestamp
- Use context managers or explicit close() for database connections
- Commit after insertions

## Testing

When adding tests:
- Test API integrations with mocked HTTP responses
- Validate error handling for missing environment variables
- Test database operations (create, read)
- Mock external API calls to avoid actual API usage

## Deployment Considerations

- Never commit API tokens or credentials to the repository
- Use `.env` file for local development (already in .gitignore)
- Environment variables must be set in production environment
- Database file should persist between restarts

## Special Notes

- The project includes both Russian and English text - this is intentional
- AI-generated content prompts are in Russian (targeting Russian-speaking audience)
- API error messages should be clear and actionable
- Rate limiting should be considered for production use

## When Making Changes

1. Preserve existing error handling patterns
2. Maintain consistent logging throughout
3. Update this file if adding new major features or dependencies
4. Consider bilingual nature of the project when adding user-facing text
5. Test API integrations thoroughly before committing
