# app/utils/voice_alert.py
from gtts import gTTS
import os
import requests
import logging

def send_voice_alert(message: str, bot_token: str, chat_id: str):
    try:
        tts = gTTS(text=message, lang='en', slow=False)
        audio_file = "alert.mp3"
        tts.save(audio_file)
        logging.info("✅ Audio generated")

        url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
        with open(audio_file, "rb") as f:
            r = requests.post(url, data={"chat_id": chat_id}, files={"voice": f})
        if r.status_code == 200:
            logging.info("📢 Voice alert sent")
        else:
            logging.error(f"❌ Telegram voice error: {r.status_code}, {r.text}")
        os.remove(audio_file)
    except Exception as e:
        logging.error(f"❌ Voice alert failed: {e}")
