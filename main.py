import json
from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection
from modules.KanjiAPIServer import KanjiAPIServer
from modules.GoogleAIAPIClient import GoogleAIAPIClient
import os
from modules.Config import Config


SAMPLE_SENTENCE_COUNT = 3

base_dir = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    # Load the JSON data
    with open('kanji.json', 'r', encoding='utf-8') as file:
        kanji_data = json.load(file)

    # Create a KanjiCollection instance
    collection = KanjiCollection()

    # Populate the collection
    for character, data in kanji_data.items():
        kanji = Kanji(character, data)
        collection.add_kanji(kanji)

    config = Config(os.path.join(base_dir, 'config.ini'))
    google_ai_api_client = GoogleAIAPIClient(api_key=config.google_api_key,
                                          model_name=config.google_model,
                                             json_response=True)

    # Initialize and run the API
    kanji_api = KanjiAPIServer(collection=collection,
                               google_ai_api_client=google_ai_api_client,
                               sample_sentence_count=SAMPLE_SENTENCE_COUNT)
    kanji_api.app.run(host='0.0.0.0', port=config.port)
