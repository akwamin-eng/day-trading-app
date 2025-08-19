# test_voice_alert.py

from gtts import gTTS
import os
import platform
import requests

# === CONFIGURE YOUR TELEGRAM ===
TELEGRAM_BOT_TOKEN = "7428894524:AAHvZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"  # Replace with your bot token
TELEGRAM_CHAT_ID = "123456789"  # Replace with your chat ID

# === TEST VOICE ALERT ===
def test_voice_alert():
    # Text to speech
    text = "This is a test. AI voice alert is working. Your trading system is online."
    print(f"🔊 Text: {text}")

    # Generate speech
    tts = gTTS(text=text, lang='en', slow=False)
    audio_file = "test_alert.mp3"
    tts.save(audio_file)
    print(f"✅ Audio saved: {audio_file}")

    # Play on Mac
    if platform.system() == "Darwin":
        os.system(f"afplay {audio_file}")
        print("▶️ Played on Mac")

    # Send to Telegram
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice"
        with open(audio_file, "rb") as f:
            response = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID},
                files={"voice": f}
            )
        if response.status_code == 200:
            print("📢 Voice message sent to Telegram ✅")
        else:
            print(f"❌ Telegram error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ Failed to send to Telegram: {e}")

    # Cleanup
    os.remove(audio_file)
    print("🧹 Cleanup complete")

if __name__ == "__main__":
    test_voice_alert()
