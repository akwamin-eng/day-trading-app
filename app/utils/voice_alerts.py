# app/utils/voice_alerts.py

from gtts import gTTS
import os
import logging

def speak_and_send(message: str, chat_id: str, bot_token: str):
    """Convert text to speech and send via Telegram"""
    try:
        tts = gTTS(text=message, lang='en', slow=False)
        audio_file = "alert.mp3"
        tts.save(audio_file)
        
        # Send via Telegram
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
        with open(audio_file, "rb") as f:
            resp = requests.post(url, data={"chat_id": chat_id}, files={"voice": f})
        if resp.ok:
            logging.info("📢 Voice alert sent to Telegram")
        else:
            logging.error(f"❌ Failed to send voice: {resp.text}")
        
        # Cleanup
        os.remove(audio_file)
    except Exception as e:
        logging.error(f"❌ Voice alert failed: {e}")
