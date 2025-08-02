# Telegram Reminder Bot with Google Docs Integration

## Deployment on Render

1. Create a new Background Worker on Render
2. Add the following environment variables:
   - `TELEGRAM_TOKEN`: Your Telegram bot token
   - `GOOGLE_DOCS_ID`: Your Google Docs document ID
3. Upload all the files from this repository
4. Set the start command to: `python bot.py`
5. Deploy!

## Google Docs Format

For best results, format your Google Docs document with questions and answers in this format:
Question 1: Answer to question 1
Question 2: Answer to question 2
The bot will match user queries with questions in the document and return the corresponding answer.
