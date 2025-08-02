import telebot
from telebot import types
import threading
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Replace with your actual Telegram Bot Token
TOKEN = '8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU'
bot = telebot.TeleBot(TOKEN)

# Google Docs configuration
GOOGLE_DOC_ID = '1wodxtiMwKBadOd8DoZpFccyqbMWRRCB8GgUEL-dFJHY'
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Path to your Google Service Account JSON file

# Dictionary to store user reminder status and intervals
user_data = {}

def get_google_doc_content():
    """Fetches content from the Google Doc"""
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
        
        return ''.join(content).strip() or "Buy now before presale end, whale 🐳 are coming, fill your bag now"
    except Exception as e:
        print(f"Error fetching Google Doc: {e}")
        return "Buy now before presale end, whale 🐳 are coming, fill your bag now"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_start = types.KeyboardButton('Start Reminders')
    btn_stop = types.KeyboardButton('Stop Reminders')
    btn_10min = types.KeyboardButton('10 min reminders')
    btn_30min = types.KeyboardButton('30 min reminders')
    btn_1hr = types.KeyboardButton('1 hour reminders')
    btn_refresh = types.KeyboardButton('Refresh Message')
    markup.add(btn_start, btn_stop, btn_10min, btn_30min, btn_1hr, btn_refresh)
    
    current_message = get_google_doc_content()
    
    bot.send_message(
        message.chat.id,
        "Welcome to the Crypto Reminder Bot!\n\n"
        "Use the buttons to control your reminders:\n"
        "- Start/Stop to control reminders\n"
        "- Choose your reminder interval\n"
        "- Refresh to update message from Google Doc\n\n"
        f"Current message: {current_message}",
        reply_markup=markup
    )
    
    # Initialize user data if not exists
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {
            'active': False,
            'interval': 1800,  # default 30 min
            'timer': None,
            'message': current_message
        }
    else:
        user_data[message.chat.id]['message'] = current_message

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    
    if chat_id not in user_data:
        user_data[chat_id] = {
            'active': False,
            'interval': 1800,  # default 30 min
            'timer': None,
            'message': get_google_doc_content()
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
    
    elif message.text == 'Refresh Message':
        new_message = get_google_doc_content()
        user_data[chat_id]['message'] = new_message
        bot.send_message(chat_id, f"Message updated from Google Doc:\n\n{new_message}")

def start_reminders(chat_id):
    if user_data[chat_id]['active']:
        # Send first reminder immediately
        bot.send_message(chat_id, user_data[chat_id]['message'])
        
        # Set up the recurring reminder
        user_data[chat_id]['timer'] = threading.Timer(
            user_data[chat_id]['interval'],
            send_reminder,
            args=[chat_id]
        )
        user_data[chat_id]['timer'].start()

def send_reminder(chat_id):
    if chat_id in user_data and user_data[chat_id]['active']:
        bot.send_message(chat_id, user_data[chat_id]['message'])
        
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
