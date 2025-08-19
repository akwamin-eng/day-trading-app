# app/utils/voice_alert.py

from gtts import gTTS
import os
import logging
import requests

def send_voice_alert(message: str, bot_token: str, chat_id: str):
    """
    Convert text to speech and send as voice message via Telegram
    """
    try:
        # Generate speech
        tts = gTTS(text=message, lang='en', slow=False)
        audio_file = "trade_alert.mp3"
        tts.save(audio_file)
        logging.info(f"✅ Audio generated: {audio_file}")

        # Send via Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
        with open(audio_file, "rb") as f:
            response = requests.post(
                url,
                data={"chat_id": chat_id},
                files={"voice": f}
            )

        if response.status_code == 200:
            logging.info("📢 Voice alert successfully sent to Telegram")
        else:
            logging.error(f"❌ Telegram API error: {response.status_code}, {response.text}")

        # Cleanup
        os.remove(audio_file)

    except Exception as e:
        logging.error(f"❌ Failed to send voice alert: {e}")
