import telebot
from telebot import types
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
import threading
import time
import re

# Configuration
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
DOCUMENT_ID = "1wodxtiMwKBadOd8DoZpFccyqbMWRRCB8GgUEL-dFJHY"
GOOGLE_CREDENTIALS_FILE = "service_account.json"  # You need to create this

bot = telebot.TeleBot(TOKEN)

# Dictionary to store document content and user sessions
document_content = ""
suggested_questions = []
user_sessions = {}

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.last_questions = []
        self.reminder_active = False
        self.reminder_interval = 30  # minutes

def fetch_document_content():
    """Fetch content from Google Docs"""
    global document_content, suggested_questions
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )
        
        service = build('docs', 'v1', credentials=credentials)
        doc = service.documents().get(documentId=DOCUMENT_ID).execute()
        
        # Extract text content
        content = []
        for elem in doc.get('body', {}).get('content', []):
            if 'paragraph' in elem:
                for para_elem in elem['paragraph']['elements']:
                    if 'textRun' in para_elem:
                        content.append(para_elem['textRun']['content'])
        
        document_content = " ".join(content)
        
        # Generate suggested questions (you can customize these)
        suggested_questions = [
            "What is iFart Token?",
            "How does iFart Token work?",
            "What are the benefits of iFart Token?",
            "How can I buy iFart Token?",
            "What makes iFart Token unique?",
            "Tell me about the iFart Token team",
            "What's the tokenomics of iFart?",
            "Where can I trade iFart Token?"
        ]
        
        return True
    except Exception as e:
        print(f"Error fetching document: {e}")
        return False

def search_document(query):
    """Search the document for relevant information"""
    if not document_content:
        return "I couldn't access the document. Please try again later."
    
    # Simple keyword-based search (you could enhance this with NLP)
    query = query.lower()
    sentences = re.split(r'[.!?]', document_content)
    
    relevant_sentences = []
    for sentence in sentences:
        if query in sentence.lower():
            relevant_sentences.append(sentence.strip())
    
    if not relevant_sentences:
        return "I couldn't find specific information about that in the document. Maybe try rephrasing your question?"
    
    return "\n\n".join(relevant_sentences[:3])  # Return up to 3 relevant sentences

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    
    # Try to fetch document content if we haven't already
    if not document_content:
        fetch_success = fetch_document_content()
        if not fetch_success:
            bot.reply_to(message, "⚠️ I'm having trouble accessing the knowledge base. Please try again later.")
            return
    
    # Create custom keyboard
    markup = types.ReplyKeyboardMarkup(row_width=2)
    
    # Add suggested questions
    for question in suggested_questions[:4]:  # Show first 4 as buttons
        markup.add(types.KeyboardButton(question))
    
    # Add reminder controls
    reminder_btn = types.KeyboardButton('🔔 Set Reminders')
    search_btn = types.KeyboardButton('🔍 Search Knowledge Base')
    markup.add(reminder_btn, search_btn)
    
    welcome_msg = """
💨 *Welcome to iFart Token Knowledge Bot!* 💨

I can answer questions about iFart Token using our official documentation.

Try one of the suggested questions or ask your own!

*Reminder feature:* Get periodic updates about iFart Token.
    """
    
    bot.send_message(message.chat.id, welcome_msg, 
                    reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    
    session = user_sessions[user_id]
    
    if message.text == '🔔 Set Reminders':
        handle_reminders(message)
    elif message.text == '🔍 Search Knowledge Base':
        bot.reply_to(message, "What would you like to know about iFart Token?")
    elif message.text in suggested_questions:
        # Handle suggested questions
        answer = search_document(message.text)
        bot.reply_to(message, answer)
        
        # Store this question in session
        session.last_questions.append(message.text)
    else:
        # Handle free-form questions
        answer = search_document(message.text)
        bot.reply_to(message, answer)
        
        # Store this question in session
        session.last_questions.append(message.text)

def handle_reminders(message):
    user_id = message.chat.id
    session = user_sessions[user_id]
    
    markup = types.ReplyKeyboardMarkup(row_width=3)
    btn_10min = types.KeyboardButton('10 min')
    btn_30min = types.KeyboardButton('30 min')
    btn_1hr = types.KeyboardButton('1 hour')
    btn_start = types.KeyboardButton('🚀 Start')
    btn_stop = types.KeyboardButton('✋ Stop')
    btn_back = types.KeyboardButton('🔙 Back')
    
    if session.reminder_active:
        status = f"Active ({session.reminder_interval} min intervals)"
    else:
        status = "Inactive"
    
    markup.add(btn_10min, btn_30min, btn_1hr, btn_start, btn_stop, btn_back)
    
    bot.send_message(
        user_id,
        f"🔔 *Reminder Settings*\n\nCurrent status: {status}\n\n"
        "Select interval or start/stop reminders:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text in ['10 min', '30 min', '1 hour'])
def set_reminder_interval(message):
    user_id = message.chat.id
    session = user_sessions[user_id]
    
    if message.text == '10 min':
        session.reminder_interval = 10
    elif message.text == '30 min':
        session.reminder_interval = 30
    elif message.text == '1 hour':
        session.reminder_interval = 60
    
    bot.reply_to(message, f"Reminder interval set to {message.text}")

@bot.message_handler(func=lambda m: m.text == '🚀 Start')
def start_reminders(message):
    user_id = message.chat.id
    session = user_sessions[user_id]
    
    if not session.reminder_active:
        session.reminder_active = True
        threading.Thread(target=send_reminders, args=(user_id,)).start()
        bot.reply_to(message, f"🚀 Reminders started! You'll get updates every {session.reminder_interval} minutes.")
    else:
        bot.reply_to(message, "Reminders are already running!")

@bot.message_handler(func=lambda m: m.text == '✋ Stop')
def stop_reminders(message):
    user_id = message.chat.id
    session = user_sessions[user_id]
    
    if session.reminder_active:
        session.reminder_active = False
        bot.reply_to(message, "✋ Reminders stopped.")
    else:
        bot.reply_to(message, "Reminders aren't currently running.")

@bot.message_handler(func=lambda m: m.text == '🔙 Back')
def back_to_main(message):
    send_welcome(message)

def send_reminders(user_id):
    session = user_sessions[user_id]
    
    while session.reminder_active:
        time.sleep(session.reminder_interval * 60)
        
        if session.reminder_active:
            # Create a dynamic reminder message based on document content
            reminder_msg = "💨 *iFart Token Reminder* 💨\n\n"
            
            # Get a random fact or update from the document
            facts = re.findall(r'\b[A-Z][^.!?]*[.!?]', document_content)
            if facts:
                reminder_msg += "Did you know?\n" + facts[len(facts)//2] + "\n\n"
            
            reminder_msg += "Whales are sniffing around 👃\nFill your bags before the wind changes! 🌬️\n\n#iFartToTheMoon 🚀"
            
            bot.send_message(user_id, reminder_msg, parse_mode='Markdown')

def periodic_document_refresh():
    """Refresh document content periodically"""
    while True:
        time.sleep(3600)  # Refresh every hour
        fetch_document_content()

if __name__ == '__main__':
    # Initial document fetch
    fetch_document_content()
    
    # Start document refresh thread
    threading.Thread(target=periodic_document_refresh, daemon=True).start()
    
    # Start bot
    bot.polling(none_stop=True)
