import os
import logging
import asyncio
import httpx
from groq import Groq

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

groq_client = Groq(api_key=GROQ_API_KEY)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def translate(text: str) -> str:
    prompt = (
        "Tu es un expert en langue ingouche (ГIалгIай мотт), langue caucasique du nord.\n"
        "Détecte la langue du texte suivant et traduis-le en ingouche.\n"
        "Si le texte est déjà en ingouche, traduis-le en russe et en français.\n"
        f"Texte : {text}\n"
        "Réponds avec la traduction uniquement, sans explication."
    )
    response = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


async def send_message(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})


async def handle_update(update: dict):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return

    if text == "/start":
        reply = (
            "🌄 Bienvenue sur le bot de traduction ingouche!\n\n"
            "Envoie n'importe quel texte en français, russe ou ingouche et je le traduirai.\n\n"
            "Exemples :\n"
            "• 'Bonjour' → traduction en ingouche\n"
            "• 'нана' → traduction en russe/français\n"
            "• 'маьрша хиллалц' → traduction\n\n"
            "ГIалгIай мотт — Langue ingouche 🏔"
        )
    else:
        try:
            await send_message(chat_id, "⏳ Traduction en cours...")
            reply = translate(text)
        except Exception as e:
            logger.error(f"Erreur traduction: {e}")
            reply = "❌ Erreur de traduction. Réessaie."

    await send_message(chat_id, reply)


async def poll():
    offset = 0
    logger.info("Bot démarré, en attente de messages...")
    async with httpx.AsyncClient(timeout=60) as client:
        while True:
            try:
                resp = await client.get(
                    f"{TELEGRAM_API}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                )
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    await handle_update(update)
            except Exception as e:
                logger.error(f"Erreur polling: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(poll())
