import json
from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection
from modules.KanjiAPIServer import KanjiAPIServer
from modules.OpenAIAPIClient import OpenAIAPIClient
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
    openai_api_client = OpenAIAPIClient(base_url=config.base_url, path=config.path, api_key=config.api_key, model=config.model, max_response_tokens=config.max_response_tokens, temperature=config.temperature)

    # Initialize and run the API
    kanji_api = KanjiAPIServer(collection=collection,
                               openai_api_client=openai_api_client,
                               sample_sentence_count=SAMPLE_SENTENCE_COUNT)
    kanji_api.app.run(host='0.0.0.0', port=5733)
