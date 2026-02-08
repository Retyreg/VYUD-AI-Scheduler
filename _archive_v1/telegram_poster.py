import os
import requests
import logging

logger = logging.getLogger(__name__)

class TelegramPoster:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set in environment")
        if not self.chat_id:
            logger.warning("TELEGRAM_CHAT_ID not set in environment")

    def post_text(self, text):
        """Post text message to Telegram channel"""
        if not self.token or not self.chat_id:
            error_msg = "Missing Telegram credentials (token or chat_id)"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {"chat_id": self.chat_id, "text": text}
        
        try:
            logger.info(f"Posting to Telegram: {text[:50]}...")
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            logger.info("Successfully posted to Telegram")
            return {"status": "success", "data": response.json()}
        except requests.exceptions.Timeout:
            error_msg = "Telegram request timeout"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"Telegram API error: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error posting to Telegram: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}