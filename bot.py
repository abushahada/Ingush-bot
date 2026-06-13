import os
import logging
import asyncio
import httpx

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

DICT = {
    "bonjour": "маьрша хиллалц", "salut": "маьрша хиллалц", "merci": "баркал",
    "oui": "хIаъ", "non": "ца хилар", "eau": "хи", "maison": "цIа",
    "mère": "нана", "père": "да", "frère": "воша", "sœur": "йиша",
    "montagne": "лоaм", "paix": "маьрша", "bien": "дика", "tête": "корта",
    "main": "куьг", "œil": "бIаьрг", "dent": "цIогI", "oreille": "лерг",
    "привет": "маьрша хиллалц", "спасибо": "баркал", "да": "хIаъ",
    "нет": "ца хилар", "вода": "хи", "дом": "цIа", "мать": "нана",
    "отец": "да", "брат": "воша", "сестра": "йиша", "гора": "лоaм",
    "хорошо": "дика", "голова": "корта", "рука": "куьг", "зуб": "цIогI",
}

async def translate(text: str) -> str:
    t = text.strip().lower()
    if t in DICT:
        return f"🏔 {DICT[t]}"

    prompt = (
        "Tu es un expert en langue ingouche (ГIалгIай мотт), langue caucasique du nord parlée en Ingouchie (Russie).\n"
        "Tu as une connaissance approfondie de la grammaire ingouche, du dictionnaire de Tarieva, et des textes classiques.\n"
        "Détecte la langue du texte et traduis-le en ingouche avec la translittération cyrillique correcte.\n"
        "Si le texte est déjà en ingouche, traduis-le en français et en russe.\n"
        f"Texte : {text}\n\n"
        "Format de réponse :\n"
        "🏔 [traduction ingouche en cyrillique]\n"
        "🇷🇺 [traduction russe]\n"
        "🇫🇷 [traduction française]"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        data = resp.json()
        return data["content"][0]["text"].strip()


async def send_message(client: httpx.AsyncClient, chat_id: int, text: str):
    await client.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})


async def poll():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{TELEGRAM_API}/getUpdates", params={"offset": -1, "timeout": 0}, timeout=10)
        data = resp.json()
        results = data.get("result", [])
        offset = (results[-1]["update_id"] + 1) if results else 0
        logger.info(f"Bot démarré avec Claude, offset: {offset}")

        while True:
            try:
                resp = await client.get(
                    f"{TELEGRAM_API}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                    timeout=40,
                )
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")

                    if not chat_id or not text:
                        continue

                    logger.info(f"Message: {text}")

                    if text.startswith("/start"):
                        reply = (
                            "🌄 Bienvenue sur le bot de traduction ingouche!\n\n"
                            "Envoie n'importe quel texte en français, russe ou ingouche.\n\n"
                            "Propulsé par Claude (Anthropic) 🤖\n"
                            "ГIалгIай мотт 🏔"
                        )
                    else:
                        await send_message(client, chat_id, "⏳ Traduction en cours...")
                        try:
                            reply = await translate(text)
                        except Exception as e:
                            logger.error(f"Erreur: {e}")
                            reply = "❌ Erreur. Réessaie."

                    await send_message(client, chat_id, reply)

            except Exception as e:
                logger.error(f"Erreur polling: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(poll())
