import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

groq_client = Groq(api_key=GROQ_API_KEY)


def translate_with_groq(text: str, target_lang: str, source_lang: str = "auto") -> str:
    if source_lang == "auto":
        prompt = (
            f"You are a professional translator specializing in the Ingush language (Гӏалгӏай мотт). "
            f"Detect the language of the following text and translate it to {target_lang}. "
            f"Return ONLY the translated text, nothing else.\n\nText: {text}"
        )
    else:
        prompt = (
            f"You are a professional translator specializing in the Ingush language (Гӏалгӏай мотт). "
            f"Translate the following text from {source_lang} to {target_lang}. "
            f"Return ONLY the translated text, nothing else.\n\nText: {text}"
        )

    response = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome = (
        "👋 Салам! Сalam!\n\n"
        "I am an Ingush language translation bot.\n\n"
        "📌 Commands:\n"
        "/toingush <text> — Translate any text TO Ingush\n"
        "/fromingush <text> — Translate Ingush text to English\n"
        "/translate <text> — Auto-detect language and translate\n"
        "/help — Show this help message\n\n"
        "Or simply send me any text and I'll translate it to Ingush automatically."
    )
    await update.message.reply_text(welcome)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🌐 *Ingush Translation Bot*\n\n"
        "*Commands:*\n"
        "`/toingush <text>` — Translate any text to Ingush\n"
        "`/fromingush <text>` — Translate Ingush to English\n"
        "`/translate <text>` — Auto-detect and translate\n\n"
        "*Or just send any message* and it will be translated to Ingush."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def to_ingush(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /toingush <text to translate>")
        return

    text = " ".join(context.args)
    await update.message.reply_text("⏳ Translating...")

    try:
        result = translate_with_groq(text, target_lang="Ingush")
        await update.message.reply_text(f"🇮🇳 *Ingush translation:*\n{result}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text("❌ Translation failed. Please try again.")


async def from_ingush(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /fromingush <Ingush text to translate>")
        return

    text = " ".join(context.args)
    await update.message.reply_text("⏳ Translating...")

    try:
        result = translate_with_groq(text, target_lang="English", source_lang="Ingush")
        await update.message.reply_text(f"🇬🇧 *English translation:*\n{result}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text("❌ Translation failed. Please try again.")


async def auto_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /translate <text>")
        return

    text = " ".join(context.args)
    await update.message.reply_text("⏳ Detecting language and translating...")

    try:
        result = translate_with_groq(text, target_lang="Ingush", source_lang="auto")
        await update.message.reply_text(f"🔄 *Translation:*\n{result}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text("❌ Translation failed. Please try again.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    await update.message.reply_text("⏳ Translating to Ingush...")

    try:
        result = translate_with_groq(text, target_lang="Ingush", source_lang="auto")
        await update.message.reply_text(f"🇮🇳 *Ingush translation:*\n{result}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text("❌ Translation failed. Please try again.")


def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("toingush", to_ingush))
    app.add_handler(CommandHandler("fromingush", from_ingush))
    app.add_handler(CommandHandler("translate", auto_translate))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started. Listening for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
