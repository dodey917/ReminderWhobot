import telebot
from telebot import types
import threading
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re

# Configuration
TOKEN = '8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU'
GOOGLE_DOC_ID = '1wodxtiMwKBadOd8DoZpFccyqbMWRRCB8GgUEL-dFJHY'
SERVICE_ACCOUNT_FILE = 'telegrambotoauth-9663d74b6c50.json'  # Your service account file

bot = telebot.TeleBot(TOKEN)
user_data = {}

class GoogleDocParser:
    def __init__(self):
        self.doc_content = ""
        self.last_updated = 0
        self.refresh_interval = 3600  # 1 hour
        
    def get_doc_content(self):
        """Fetch and cache the Google Doc content"""
        current_time = time.time()
        if current_time - self.last_updated > self.refresh_interval:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_FILE,
                    scopes=['https://www.googleapis.com/auth/documents.readonly']
                )
                
                service = build('docs', 'v1', credentials=credentials)
                doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
                
                content = []
                for elem in doc.get('body', {}).get('content', []):
                    if 'paragraph' in elem:
                        for text_run in elem['paragraph'].get('elements', []):
                            if 'textRun' in text_run:
                                content.append(text_run['textRun']['content'])
                
                self.doc_content = ''.join(content).strip()
                self.last_updated = current_time
            except Exception as e:
                print(f"Error fetching Google Doc: {e}")
                if not self.doc_content:
                    self.doc_content = "Buy now before presale end, whale 🐳 are coming, fill your bag now"
        
        return self.doc_content
    
    def find_answer(self, question):
        """Search for answers in the document based on the question"""
        content = self.get_doc_content()
        
        # Simple keyword-based answer extraction
        question_lower = question.lower()
        
        if 'what is ifart' in question_lower or 'about ifart' in question_lower:
            # Extract the introductory section
            intro_match = re.search(r'1\. Brief Intro(.+?)(?=\n\d\.|\Z)', content, re.DOTALL)
            if intro_match:
                return intro_match.group(1).strip()
        
        elif 'tokenomics' in question_lower or 'economic' in question_lower:
            # Look for tokenomics section
            tokenomics_match = re.search(r'(Tokenomics|Economic.+\n)(.+?)(?=\n\d\.|\Z)', content, re.DOTALL|re.IGNORECASE)
            if tokenomics_match:
                return tokenomics_match.group(2).strip()
        
        elif 'disclaimer' in question_lower or 'risk' in question_lower:
            # Find disclaimer section
            disclaimer_match = re.search(r'DISCLAIMER(.+?)(?=\n\d\.|\Z)', content, re.DOTALL)
            if disclaimer_match:
                return disclaimer_match.group(1).strip()
        
        elif 'roadmap' in question_lower or 'plan' in question_lower:
            # Find roadmap section
            roadmap_match = re.search(r'(Roadmap|Future Plans.+\n)(.+?)(?=\n\d\.|\Z)', content, re.DOTALL|re.IGNORECASE)
            if roadmap_match:
                return roadmap_match.group(2).strip()
        
        # Default response if no specific section matches
        return f"I couldn't find a specific answer to your question in the document. Here's the general information about iFart:\n\n{content[:1500]}..." if len(content) > 1500 else content

doc_parser = GoogleDocParser()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_start = types.KeyboardButton('Start Reminders')
    btn_stop = types.KeyboardButton('Stop Reminders')
    btn_10min = types.KeyboardButton('10 min reminders')
    btn_30min = types.KeyboardButton('30 min reminders')
    btn_1hr = types.KeyboardButton('1 hour reminders')
    btn_refresh = types.KeyboardButton('Refresh Content')
    markup.add(btn_start, btn_stop, btn_10min, btn_30min, btn_1hr, btn_refresh)
    
    current_message = doc_parser.get_doc_content()[:500] + "..." if len(doc_parser.get_doc_content()) > 500 else doc_parser.get_doc_content()
    
    bot.send_message(
        message.chat.id,
        "Welcome to the iFart Token Info Bot!\n\n"
        "I can provide information from the iFart whitepaper and send you regular reminders.\n\n"
        "Available commands:\n"
        "- Ask any question about iFart\n"
        "- Use buttons to control reminders\n"
        "- 'Refresh Content' to update from Google Doc\n\n"
        f"Current document preview:\n{current_message}",
        reply_markup=markup
    )
    
    # Initialize user data if not exists
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {
            'active': False,
            'interval': 1800,  # default 30 min
            'timer': None
        }

@bot.message_handler(func=lambda message: message.text in [
    'Start Reminders', 'Stop Reminders', 
    '10 min reminders', '30 min reminders', 
    '1 hour reminders', 'Refresh Content'
])
def handle_buttons(message):
    chat_id = message.chat.id
    
    if chat_id not in user_data:
        user_data[chat_id] = {
            'active': False,
            'interval': 1800,
            'timer': None
        }
    
    if message.text == 'Start Reminders':
        if not user_data[chat_id]['active']:
            user_data[chat_id]['active'] = True
            start_reminders(chat_id)
            bot.send_message(chat_id, "Reminders started! 🚀")
        else:
            bot.send_message(chat_id, "Reminders are already running!")
    
    elif message.text == 'Stop Reminders':
        if user_data[chat_id]['active']:
            user_data[chat_id]['active'] = False
            if user_data[chat_id]['timer']:
                user_data[chat_id]['timer'].cancel()
            bot.send_message(chat_id, "Reminders stopped. ⏹")
        else:
            bot.send_message(chat_id, "Reminders aren't running!")
    
    elif message.text == '10 min reminders':
        user_data[chat_id]['interval'] = 600
        bot.send_message(chat_id, "Reminder interval set to 10 minutes ⏰")
        if user_data[chat_id]['active']:
            if user_data[chat_id]['timer']:
                user_data[chat_id]['timer'].cancel()
            start_reminders(chat_id)
    
    elif message.text == '30 min reminders':
        user_data[chat_id]['interval'] = 1800
        bot.send_message(chat_id, "Reminder interval set to 30 minutes ⏰")
        if user_data[chat_id]['active']:
            if user_data[chat_id]['timer']:
                user_data[chat_id]['timer'].cancel()
            start_reminders(chat_id)
    
    elif message.text == '1 hour reminders':
        user_data[chat_id]['interval'] = 3600
        bot.send_message(chat_id, "Reminder interval set to 1 hour ⏰")
        if user_data[chat_id]['active']:
            if user_data[chat_id]['timer']:
                user_data[chat_id]['timer'].cancel()
            start_reminders(chat_id)
    
    elif message.text == 'Refresh Content':
        doc_parser.last_updated = 0  # Force refresh
        content_preview = doc_parser.get_doc_content()[:500] + "..." if len(doc_parser.get_doc_content()) > 500 else doc_parser.get_doc_content()
        bot.send_message(chat_id, f"Document content refreshed!\n\nPreview:\n{content_preview}")

@bot.message_handler(func=lambda message: True)
def handle_questions(message):
    chat_id = message.chat.id
    question = message.text
    
    # Don't process button commands as questions
    if message.text in [
        'Start Reminders', 'Stop Reminders', 
        '10 min reminders', '30 min reminders', 
        '1 hour reminders', 'Refresh Content'
    ]:
        return
    
    answer = doc_parser.find_answer(question)
    bot.send_message(chat_id, answer)

def start_reminders(chat_id):
    if user_data[chat_id]['active']:
        # Send first reminder immediately
        bot.send_message(chat_id, doc_parser.get_doc_content()[:2000])  # Truncate if too long
        
        # Set up the recurring reminder
        user_data[chat_id]['timer'] = threading.Timer(
            user_data[chat_id]['interval'],
            send_reminder,
            args=[chat_id]
        )
        user_data[chat_id]['timer'].start()

def send_reminder(chat_id):
    if chat_id in user_data and user_data[chat_id]['active']:
        bot.send_message(chat_id, doc_parser.get_doc_content()[:2000])  # Truncate if too long
        
        # Schedule the next reminder
        user_data[chat_id]['timer'] = threading.Timer(
            user_data[chat_id]['interval'],
            send_reminder,
            args=[chat_id]
        )
        user_data[chat_id]['timer'].start()

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
