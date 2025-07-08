import os
import json
import logging
import time
import re
from modules.Config import Config
from modules.GoogleAIAPIClient import GoogleAIAPIClient
from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SentenceGenerator:
    INVALID_CHARS = {'\\'}
    def __init__(self, kanji_json_path: str,
                 categories_dir: str,
                 config_path: str,
                 max_attempts_per_kanji: int = 5,
                 sleep_seconds: int = 3,
                 sentence_count: int = 3,
                 skip_existing: bool = False):
        self.kanji_json_path = kanji_json_path
        self.categories_dir = categories_dir
        self.sentence_count = sentence_count
        self.config = Config(config_path)
        self.skip_existing = skip_existing
        self.sleep_seconds = sleep_seconds
        self.api_client = GoogleAIAPIClient(api_key=self.config.google_api_key,
                                            model_name=self.config.google_model,
                                            json_response=True)
        self.max_attempts_per_kanji = max_attempts_per_kanji

        if not os.path.exists(self.categories_dir):
            os.makedirs(self.categories_dir)
            logger.info(f"Created base directory: {self.categories_dir}")

        logger.info(f"Invalid characters set: {self.INVALID_CHARS}")

    def is_valid_sentence_entry(self, entry: dict) -> bool:
        sentence = entry.get('sentence', '')
        sentence_furigana = entry.get('sentence_furigana', '')

        if not sentence:
            logger.error("Invalid: 'sentence' is empty/missing.")
            return False

        if not sentence_furigana:
            logger.error("Invalid: 'sentence_furigana' is empty/missing.")
            return False

        # If "sentence" contains 【 or 】 → invalid
        if '【' in sentence or '】' in sentence:
            logger.error(f"Invalid: 'sentence' contains 【 or 】 → {sentence}")
            return False

        # Calculate Japanese character proportion
        # Exclude punctuation 【 】 。 ー and spaces
        cleaned = re.sub(r'[【】。、ー\s]', '', sentence)
        total_chars = len(cleaned)

        # Count Japanese chars and numbers
        japanese_chars = re.findall(r'[\u3040-\u30FF\u4E00-\u9FFF0-9]', cleaned)
        japanese_count = len(japanese_chars)

        if total_chars == 0:
            logger.error(f"Invalid: no valid chars in → {sentence}")
            return False

        proportion = japanese_count / total_chars
        if proportion != 1:
            logger.info(f"Proportion Japanese: {proportion:.2f} for sentence: {sentence}")

        if proportion < 0.85:
            logger.error(f"Invalid: too low JP proportion for sentence '{sentence}'")
            return False

            # Basic furigana check for safety
        if "【" not in sentence_furigana or "】" not in sentence_furigana:
            logger.warning(f"Missing furigana brackets in sentence_furigana '{sentence_furigana}'")
            return False

        if any(char in sentence for char in self.INVALID_CHARS):
            logger.error(f"Invalid: 'sentence' contains invalid character(s): {sentence}")
            return False

        if any(char in sentence_furigana for char in self.INVALID_CHARS):
            logger.error(f"Invalid: 'sentence_furigana' contains invalid character(s): {sentence_furigana}")
            return False

        return True

    def validate_response(self, parsed_response) -> bool:
        if not isinstance(parsed_response, list):
            logger.warning("Parsed response is not a list.")
            return False

        for entry in parsed_response:
            if not isinstance(entry, dict):
                logger.warning(f"Entry is not a dictionary: {entry}")
                return False

            if not self.is_valid_sentence_entry(entry):
                logger.warning(f"Invalid sentence entry detected: {entry}")
                return False

        return True

    def generate_for_all(self):
        with open(self.kanji_json_path, 'r', encoding='utf-8') as f:
            kanji_data = json.load(f)

        collection = KanjiCollection(categories_dir=self.categories_dir)
        for character, data in kanji_data.items():
            kanji = Kanji(character, data)
            collection.add_kanji(kanji, require_sample_sentences=False)

        jlpt_kanji = collection.n5 + collection.n4 + collection.n3 + collection.n2 + collection.n1

        total_characters = len(jlpt_kanji)
        attempted = 0
        already_exists = 0
        success_count = 0
        failed_characters = []

        logger.info(f"Starting sentence generation for {total_characters} JLPT kanji (N5–N1)...")

        for index, kanji in enumerate(jlpt_kanji, start=1):
            character = kanji.character
            logger.info(f"[{index}/{total_characters}] Generating sentences for: {character}")
            attempted += 1

            prompt = kanji.get_example_sentences_prompt(self.sentence_count)
            if not prompt:
                logger.warning(f"Skipped {character} due to missing prompt.")
                failed_characters.append(character)
                time.sleep(self.sleep_seconds)
                continue

            jlpt_level_str = f"N{kanji.jlpt_new}"
            jlpt_dir = os.path.join(self.categories_dir, jlpt_level_str)
            os.makedirs(jlpt_dir, exist_ok=True)
            output_path = os.path.join(jlpt_dir, character, f"{character}.json")
            logger.info(f"Output path for {character}: {output_path}")

            if self.skip_existing and os.path.exists(output_path):
                logger.info(f"Skipping existing file for {character}: {output_path}")
                success_count += 1
                already_exists += 1
                continue

            success = False
            attempt = 0

            while not success and attempt < self.max_attempts_per_kanji:
                attempt += 1
                try:
                    response = self.api_client.send_prompt(prompt)

                    parsed_response = json.loads(response)

                    if not self.validate_response(parsed_response):
                        logger.warning(f"Attempt {attempt}: Invalid response for {character}. Retrying...")
                        continue

                    character_dir = os.path.join(jlpt_dir, character)
                    os.makedirs(character_dir, exist_ok=True)

                    with open(output_path, 'w', encoding='utf-8') as out_file:
                        json.dump(parsed_response, out_file, ensure_ascii=False, indent=2)

                    logger.info(f"Wrote {character} sample sentences to {output_path}")
                    success = True
                    success_count += 1

                except Exception as e:
                    logger.error(f"Attempt {attempt}: Failed to process {character}: {e}")

                finally:
                    time.sleep(self.sleep_seconds)

            if not success:
                failed_characters.append(character)
                logger.error(f"Gave up on {character} after {self.max_attempts_per_kanji} attempts.")

        logger.info("==== Sentence Generation Summary ====")
        logger.info(f"Total JLPT Kanji: {total_characters}")
        logger.info(f"Already Exists: {already_exists}")
        logger.info(f"Attempted: {attempted}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {len(failed_characters)}")

        if failed_characters:
            logger.info("Failed Kanji:")
            for char in failed_characters:
                logger.info(f" - {char}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kanji_json = os.path.join(base_dir, '..', 'kanji_data', 'kanji.json')
    config_ini = os.path.join(base_dir, '..', 'config.ini')
    categories_directory = os.path.join(base_dir, '..', 'kanji_data', "categories")

    generator = SentenceGenerator(
        kanji_json_path=kanji_json,
        categories_dir=categories_directory,
        config_path=config_ini,
        max_attempts_per_kanji=5,
        sleep_seconds=1,
        sentence_count=100,
        skip_existing=True
    )
    generator.generate_for_all()
