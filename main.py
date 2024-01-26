import json
import random
from typing import List, Optional
from flask import Flask, Response

class Kanji:
    def __init__(self, character: str, data: dict):
        self.character = character
        self.strokes = data['strokes']
        self.grade = data['grade']
        self.freq = data['freq']
        self.jlpt_old = data['jlpt_old']
        self.jlpt_new = data['jlpt_new']
        self.meanings = data['meanings']
        self.readings_on = data['readings_on']
        self.readings_kun = data['readings_kun']
        self.wk_level = data['wk_level']
        self.wk_meanings = data['wk_meanings']
        self.wk_readings_on = data['wk_readings_on']
        self.wk_readings_kun = data['wk_readings_kun']
        self.wk_radicals = data['wk_radicals']

class KanjiCollection:
    def __init__(self):
        self.n1 = []
        self.n2 = []
        self.n3 = []
        self.n4 = []
        self.n5 = []

    def add_kanji(self, kanji: Kanji):
        jlpt_new = kanji.jlpt_new
        if jlpt_new is None:
            return
        if jlpt_new == 1:
            self.n1.append(kanji)
        elif jlpt_new == 2:
            self.n2.append(kanji)
        elif jlpt_new == 3:
            self.n3.append(kanji)
        elif jlpt_new == 4:
            self.n4.append(kanji)
        elif jlpt_new == 5:
            self.n5.append(kanji)

    def get_random_kanji(self, jlpt_levels: List[int]) -> Optional[Kanji]:
        kanji_pool = []
        for level in jlpt_levels:
            kanji_pool.extend(getattr(self, f'n{level}', []))
        return random.choice(kanji_pool) if kanji_pool else None

class KanjiAPI:
    def __init__(self, collection: KanjiCollection):
        self.collection = collection
        self.app = Flask(__name__)
        self.app.add_url_rule('/random_kanji/', 'get_kanji', self.get_kanji, methods=['GET'], defaults={'levels': ''})
        self.app.add_url_rule('/random_kanji/<levels>', 'get_kanji', self.get_kanji, methods=['GET'])


    def get_kanji(self, levels: str = '') -> Response:
        if levels:
            try:
                # Filter out empty strings after splitting
                jlpt_levels = [int(level) for level in levels.split(',') if level.strip()]
            except ValueError:
                return Response("Invalid JLPT level format.", status=400)
        else:
            # If no level is specified, use all levels
            jlpt_levels = [1, 2, 3, 4, 5]

        kanji = self.collection.get_random_kanji(jlpt_levels)
        if kanji:
            return Response(self.format_kanji_info(kanji), mimetype='text/plain')
        else:
            return Response("No kanji found for the specified JLPT levels.", status=404)



    @staticmethod
    def format_kanji_info(kanji: Kanji) -> str:
        info = [
            f"Character: {kanji.character}",
            f"Strokes: {kanji.strokes}",
            f"Grade: {kanji.grade}",
            f"Frequency: {kanji.freq}",
            f"JLPT (old): {kanji.jlpt_old}",
            f"JLPT (new): {kanji.jlpt_new}",
            f"Meanings: {', '.join(kanji.meanings)}",
            f"On readings: {', '.join(kanji.readings_on)}",
            f"Kun readings: {', '.join(kanji.readings_kun)}",
            # Include other fields if needed
        ]
        return '\n'.join(info)


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

    # Initialize and run the API
    kanji_api = KanjiAPI(collection)
    kanji_api.app.run(host='0.0.0.0', port=5733)