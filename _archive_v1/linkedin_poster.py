import os
import requests
import logging

logger = logging.getLogger(__name__)

class LinkedinPoster:
    def __init__(self):
        self.token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        self.api_url = "https://api.linkedin.com/v2/shares"
        
        if not self.token:
            logger.warning("LINKEDIN_ACCESS_TOKEN not set in environment")

    def post_text(self, text):
        """Post text message to LinkedIn platform"""
        if not self.token:
            error_msg = "Missing LinkedIn access token"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "owner": os.environ.get("LINKEDIN_PROFILE_ID"),
            "text": {
                "text": text
            }
        }
        
        try:
            logger.info(f"Posting to LinkedIn: {text[:50]}...")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Successfully posted to LinkedIn")
            return {"status": "success", "data": response.json()}
        except requests.exceptions.Timeout:
            error_msg = "LinkedIn API request timeout"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"LinkedIn API error: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error posting to LinkedIn: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}