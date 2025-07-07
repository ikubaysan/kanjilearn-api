import json
from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection
import os
from modules.Config import Config
from modules.Utils import *
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    # Load the JSON data
    with open('../kanji_data/kanji.json', 'r', encoding='utf-8') as file:
        kanji_data = json.load(file)

    # Create a KanjiCollection instance
    categories_dir = os.path.join(base_dir, '../kanji_data/categories')
    collection = KanjiCollection(categories_dir=categories_dir)

    # Populate the collection
    max_kanji_definition_len = 0
    max_kanji_info_with_meanings_len = 0
    for character, data in kanji_data.items():
        kanji = Kanji(character, data)
        collection.add_kanji(kanji)

        this_kanji_definition_len = 0
        this_kanji_info_with_meanings_len = 0
        for meaning in kanji.meanings:
            this_kanji_definition_len += len(meaning)

        if this_kanji_definition_len > max_kanji_definition_len:
            max_kanji_definition_len = this_kanji_definition_len

        # Sort kanji.sample_sentences by length of sentence
        sorted_sample_sentences = sorted(kanji.sample_sentences, key=lambda x: len(x.sentence), reverse=True)
        # Get the top 3 longest sample sentences
        top_sample_sentences = sorted_sample_sentences[:3]

        kanji_info_with_meanings = format_kanji_info(sample_sentences=top_sample_sentences,
                                                     kanji=kanji,
                                                        include_meanings=True,
                                                     )

        this_kanji_info_with_meanings_len = len(kanji_info_with_meanings)
        if this_kanji_info_with_meanings_len > max_kanji_info_with_meanings_len:
            max_kanji_info_with_meanings_len = this_kanji_info_with_meanings_len

    logger.info(f"Max kanji definition length: {max_kanji_definition_len}")
    logger.info(f"Max kanji info with meanings length: {max_kanji_info_with_meanings_len}")
