import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from deepgram import Deepgram
import config
import io

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Deepgram client
deepgram = Deepgram(config.DEEPGRAM_API_KEY)

# Language options
LANGUAGES = {
    "en": "English 🇬🇧",
    "es": "Spanish 🇪🇸",
    "fr": "French 🇫🇷",
    "de": "German 🇩🇪",
    "it": "Italian 🇮🇹",
    "pt": "Portuguese 🇵🇹",
    "nl": "Dutch 🇳🇱",
    "ja": "Japanese 🇯🇵",
    "ko": "Korean 🇰🇷",
    "zh": "Chinese 🇨🇳"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I can transcribe voice messages. Send me a voice message or audio file to get started."
    )
    await show_language_options(update, context)

async def show_language_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection options."""
    keyboard = [
        [InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}") 
         for lang_code, lang_name in list(LANGUAGES.items())[:5]],
        [InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}") 
         for lang_code, lang_name in list(LANGUAGES.items())[5:]]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please select the language of the audio:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        context.user_data["language"] = lang
        await query.edit_message_text(f"Language set to {LANGUAGES[lang]}. You can now send me a voice message or audio file.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages and audio files."""
    if "language" not in context.user_data:
        await update.message.reply_text("Please select a language first using the /start command.")
        return

    if update.message.voice:
        file_id = update.message.voice.file_id
    elif update.message.audio:
        file_id = update.message.audio.file_id
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('audio/'):
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("Please send a voice message or an audio file.")
        return

    file = await context.bot.get_file(file_id)
    file_url = file.file_path

    options = {
        "model": "nova-2",
        "smart_format": True,
        "language": context.user_data["language"]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url)
            audio_data = response.content

            transcription_response = await deepgram.transcription.prerecorded(
                buffer=audio_data,
                mimetype='audio/mpeg',  # You may need to adjust the MIME type based on your audio file format
                **options
            )
            transcript = transcription_response['results']['channels'][0]['alternatives'][0]['transcript']

            if len(transcript) > 4096:  # Telegram message length limit
                with io.StringIO(transcript) as transcript_file:
                    await update.message.reply_document(document=transcript_file, filename="transcription.txt")
            else:
                await update.message.reply_text(transcript)
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        await update.message.reply_text("Sorry, there was an error processing your audio. Please try again.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.Document.AUDIO, handle_voice))

    application.run_polling()

if __name__ == '__main__':
    main()
