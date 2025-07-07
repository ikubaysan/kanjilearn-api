import json
from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection
from modules.KanjiAPIServer import KanjiAPIServer
from modules.GoogleAIAPIClient import GoogleAIAPIClient
import os
from modules.Config import Config
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    # Load the JSON data
    with open('./kanji_data/kanji.json', 'r', encoding='utf-8') as file:
        kanji_data = json.load(file)

    # Create a KanjiCollection instance
    categories_dir = os.path.join(base_dir, './kanji_data/categories')
    collection = KanjiCollection(categories_dir=categories_dir)

    # Populate the collection
    for character, data in kanji_data.items():
        kanji = Kanji(character, data)
        collection.add_kanji(kanji)

    config = Config(os.path.join(base_dir, 'config.ini'))

    logger.info(f"Starting Kanji API server with configuration: {config.to_dict()}")

    # Initialize and run the API
    kanji_api = KanjiAPIServer(collection=collection,
                               public_hostname=config.public_hostname,
                               port=config.port,
                               max_chars_per_audio_url=config.max_chars_per_audio_url,
                               max_chars_per_quiz_answer=config.quiz_max_chars_per_answer,
                               max_chars_per_kanji_info_section=config.quiz_max_chars_per_kanji_info_section,
                               quiz_potential_answers_count=config.quiz_potential_answers_count,
                               sample_sentence_count=config.sample_sentence_count,
                               )
    kanji_api.app.run(host=config.private_hostname, port=config.port)
