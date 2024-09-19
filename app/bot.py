import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import config
import io
from deepgram import DeepgramClient, DeepgramClientOptions
import asyncio

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Language options
LANGUAGES = {
    "en-US": "English 🇬🇧 ",
    "nl": "Dutch 🇳🇱 "
}

# Default language
DEFAULT_LANGUAGE = "nl"

# Initialize the Deepgram client
deepgram = DeepgramClient(config.DEEPGRAM_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if str(update.effective_user.id) != config.ALLOWED_USER_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I can transcribe voice messages. Send me a voice message or audio file to get started."
    )
    await show_language_options(update, context)

async def show_language_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection options."""
    if str(update.effective_user.id) != config.ALLOWED_USER_ID:
        return

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
    if str(update.effective_user.id) != config.ALLOWED_USER_ID:
        await update.callback_query.answer("You are not authorized to use this bot.")
        return

    query = update.callback_query
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        context.user_data["language"] = lang
        await query.edit_message_text(f"Language set to {LANGUAGES[lang]}. You can now send me a voice message or audio file.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages and audio files."""
    if str(update.effective_user.id) != config.ALLOWED_USER_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    if "language" not in context.user_data:
        context.user_data["language"] = DEFAULT_LANGUAGE
        await update.message.reply_text(f"Using default language: {LANGUAGES[DEFAULT_LANGUAGE]}. You can change it using the /start command.")

    file = None
    mime_type = None

    if update.message.voice:
        file = await context.bot.get_file(update.message.voice.file_id)
        mime_type = "audio/ogg"
    elif update.message.audio:
        file = await context.bot.get_file(update.message.audio.file_id)
        mime_type = update.message.audio.mime_type
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('audio/'):
        file = await context.bot.get_file(update.message.document.file_id)
        mime_type = update.message.document.mime_type
    else:
        await update.message.reply_text("Please send a voice message or an audio file.")
        return

    if not file:
        await update.message.reply_text("Sorry, I couldn't process that file. Please try again.")
        return

    file_url = file.file_path

    try:
        # Set up options for transcription
        options = {
            "smart_format": True,
            "model": "nova-2",
            "language": context.user_data["language"],
            "detect_language": True
        }

        # Request transcription
        response = await deepgram.transcription.prerecorded.v("1").transcribe_url(
            {"url": file_url},
            options
        )

        # Process the response
        transcript = response.results.channels[0].alternatives[0].transcript
        detected_language = response.results.channels[0].detected_language

        response_text = f"Detected language: {detected_language}\n\nTranscript:\n{transcript}"

        if len(response_text) > 4096:  # Telegram message length limit
            with io.StringIO(response_text) as transcript_file:
                await update.message.reply_document(document=transcript_file, filename="transcription.txt")
        else:
            await update.message.reply_text(response_text)

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