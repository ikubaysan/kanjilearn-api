import google.generativeai as genai
import time
import logging
from modules.Config import Config

logger = logging.getLogger(__name__)

class GoogleAIAPIClient:
    def __init__(self, api_key: str, model_name: str, json_response: bool = False):
        self.api_key = api_key
        self.model_name = model_name

        # See:
        # https://stackoverflow.com/a/78078401/8151234
        # https://ai.google.dev/gemini-api/docs/safety-settings
        # These are the 4 safety categories, and default threshold is "BLOCK_MEDIUM_AND_ABOVE". Let's disable them.
        self.safe = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            }
        ]

        genai.configure(api_key=api_key)

        if json_response:
            self.model = genai.GenerativeModel(model_name=model_name,
                                               generation_config={"response_mime_type": "application/json"})
        else:
            self.model = genai.GenerativeModel(model_name=model_name)
        logger.info(f"Google AI API client initialized with model {model_name}")
        return

    def send_prompt(self, prompt: str) -> str:
        # logger.info(f"Sending prompt to Google AI API with model {self.model_name}: '{prompt[:50]}...'")
        response = self.model.generate_content(prompt, safety_settings=self.safe)
        response_text = response.text

        return response_text


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    from modules.Config import Config
    config = Config('../config.ini')

    google_ai_api_client = GoogleAIAPIClient(api_key=config.google_api_key,
                                          model_name=config.google_model)

    response = google_ai_api_client.send_prompt(prompt="What is the capital of France?")
    logger.info(f"Got response: {response}")