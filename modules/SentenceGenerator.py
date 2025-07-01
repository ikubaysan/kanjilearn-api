import os
import json
import logging
import time
from modules.Config import Config
from modules.GoogleAIAPIClient import GoogleAIAPIClient
from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SentenceGenerator:
    def __init__(self, kanji_json_path: str, output_dir: str, config_path: str, sleep_seconds: int = 3, sentence_count: int = 3, skip_existing: bool = False):
        self.kanji_json_path = kanji_json_path
        self.output_dir = output_dir
        self.sentence_count = sentence_count
        self.config = Config(config_path)
        self.skip_existing = skip_existing
        self.sleep_seconds = sleep_seconds
        self.api_client = GoogleAIAPIClient(api_key=self.config.google_api_key,
                                            model_name=self.config.google_model,
                                            json_response=True)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created base directory: {self.output_dir}")

    def generate_for_all(self):
        with open(self.kanji_json_path, 'r', encoding='utf-8') as f:
            kanji_data = json.load(f)

        # Build JLPT-only KanjiCollection
        collection = KanjiCollection(categories_dir=self.output_dir)
        for character, data in kanji_data.items():
            kanji = Kanji(character, data)
            collection.add_kanji(kanji, require_sample_sentences=False)

        # Combine kanji from N5 to N1
        jlpt_kanji = collection.n5 + collection.n4 + collection.n3 + collection.n2 + collection.n1

        total_characters = len(jlpt_kanji)
        attempted = 0
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
                time.sleep(3)
                continue

            # Subfolder by JLPT level (e.g., N5, N4, ...)
            jlpt_level_str = f"N{kanji.jlpt_new}"
            jlpt_dir = os.path.join(self.output_dir, jlpt_level_str)
            os.makedirs(jlpt_dir, exist_ok=True)
            output_path = os.path.join(jlpt_dir, character, f"{character}.json")
            logger.info(f"Output path for {character}: {output_path}")

            if self.skip_existing and os.path.exists(output_path):
                logger.info(f"Skipping existing file for {character}: {output_path}")
                success_count += 1
                continue

            success = False
            attempt = 0

            while not success and attempt < 3:
                attempt += 1
                try:
                    response = self.api_client.send_prompt(prompt)
                    if "【" not in response or "】" not in response:
                        logger.warning(f"Attempt {attempt}: Missing furigana brackets in response for {character}. Retrying...")
                        continue

                    parsed_response = json.loads(response)

                    # Create folder for the character if it doesn't exist
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
                    time.sleep(3)

            if not success:
                failed_characters.append(character)
                logger.error(f"Gave up on {character} after 3 attempts.")

        # Final Summary
        logger.info("==== Sentence Generation Summary ====")
        logger.info(f"Total JLPT Kanji: {total_characters}")
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
    output_directory = os.path.join(base_dir, '..', 'kanji_data')

    generator = SentenceGenerator(
        kanji_json_path=kanji_json,
        output_dir=output_directory,
        config_path=config_ini,
        sleep_seconds=1,
        sentence_count=100,
        skip_existing=True
    )
    generator.generate_for_all()
