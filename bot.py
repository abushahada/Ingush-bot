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


async def send_message(client: httpx.AsyncClient, chat_id: int, text: str):
    await client.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})


async def get_updates(client: httpx.AsyncClient, offset: int):
    resp = await client.get(
        f"{TELEGRAM_API}/getUpdates",
        params={"offset": offset, "timeout": 30},
        timeout=40,
    )
    return resp.json()


async def poll():
    # D'abord vider la file des anciens messages
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{TELEGRAM_API}/getUpdates", params={"offset": -1, "timeout": 0}, timeout=10)
        data = resp.json()
        results = data.get("result", [])
        offset = (results[-1]["update_id"] + 1) if results else 0
        logger.info(f"Bot démarré, offset initial: {offset}")

        while True:
            try:
                data = await get_updates(client, offset)
                for update in data.get("result", []):
                    update_id = update["update_id"]
                    offset = update_id + 1
                    logger.info(f"Nouveau message reçu! update_id={update_id}")

                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")

                    if not chat_id or not text:
                        continue

                    logger.info(f"Message de {chat_id}: {text}")

                    if text.startswith("/start"):
                        reply = (
                            "🌄 Bienvenue sur le bot de traduction ingouche!\n\n"
                            "Envoie n'importe quel texte en français, russe ou ingouche.\n\n"
                            "ГIалгIай мотт 🏔"
                        )
                    else:
                        await send_message(client, chat_id, "⏳ Traduction en cours...")
                        try:
                            reply = translate(text)
                        except Exception as e:
                            logger.error(f"Erreur traduction: {e}")
                            reply = "❌ Erreur. Réessaie."

                    await send_message(client, chat_id, reply)
                    logger.info(f"Réponse envoyée: {reply[:50]}")

            except Exception as e:
                logger.error(f"Erreur polling: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(poll())
