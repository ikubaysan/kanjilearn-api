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

    def get_random_kanji(self, jlpt_level: int) -> Optional[Kanji]:
        if jlpt_level == 1:
            return random.choice(self.n1) if self.n1 else None
        elif jlpt_level == 2:
            return random.choice(self.n2) if self.n2 else None
        elif jlpt_level == 3:
            return random.choice(self.n3) if self.n3 else None
        elif jlpt_level == 4:
            return random.choice(self.n4) if self.n4 else None
        elif jlpt_level == 5:
            return random.choice(self.n5) if self.n5 else None
        else:
            return None

class KanjiAPI:
    def __init__(self, collection: KanjiCollection):
        self.collection = collection
        self.app = Flask(__name__)
        self.app.add_url_rule('/<int:jlpt_level>', 'get_kanji', self.get_kanji, methods=['GET'])

    def get_kanji(self, jlpt_level: int) -> Response:
        kanji = self.collection.get_random_kanji(jlpt_level)
        if kanji:
            return Response(self.format_kanji_info(kanji), mimetype='text/plain')
        else:
            return Response("No kanji found for the specified JLPT level.", status=404)

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