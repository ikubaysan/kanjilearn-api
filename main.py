import json
import random
from typing import List, Optional
from flask import Flask, Response

SAMPLE_SENTENCE_COUNT = 3

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
        self.app.add_url_rule('/quiz/', 'quiz_kanji', self.quiz_kanji, methods=['GET'], defaults={'levels': ''})
        self.app.add_url_rule('/quiz/<levels>', 'quiz_kanji', self.quiz_kanji, methods=['GET'])

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
            response = f"{kanji.character}@{self.format_kanji_info(kanji, include_meanings=True, sample_sentence_count=SAMPLE_SENTENCE_COUNT)}"
            return Response(response, mimetype='text/plain')
        else:
            return Response("No kanji found for the specified JLPT levels.", status=404)

    def quiz_kanji(self, levels: str = '') -> Response:
        if levels:
            try:
                jlpt_levels = [int(level) for level in levels.split(',') if level.strip()]
            except ValueError:
                return Response("Invalid JLPT level format.", status=400)
        else:
            jlpt_levels = [1, 2, 3, 4, 5]

        quiz_kanji = [self.collection.get_random_kanji(jlpt_levels) for _ in range(5)]
        if not all(quiz_kanji):
            return Response("Insufficient kanji data for the quiz.", status=404)

        first_kanji_info = self.format_kanji_info(quiz_kanji[0], include_meanings=False)
        meanings = [kanji.meanings for kanji in quiz_kanji]
        random.shuffle(meanings)
        correct_answer_index = meanings.index(quiz_kanji[0].meanings)

        response = f"{quiz_kanji[0].character}@{first_kanji_info}@{'@'.join([', '.join(m) for m in meanings])}@{correct_answer_index}"
        return Response(response, mimetype='text/plain')


    def get_sample_sentences(self, kanji: Kanji, count: int = 1) -> List[str]:
        sentences = []
        for i in range(count):
            # TODO: use AI to generate sample sentences
            sentence = f"This is sample sentence #{i + 1} for {kanji.character}."
            sentences.append(sentence)
        return sentences

    def format_kanji_info(self, kanji: Kanji, include_meanings: bool = True, sample_sentence_count: int = 0) -> str:
        info = [
            f"画数: {kanji.strokes}",
            f"学年: {kanji.grade}",
            f"JLPT: {kanji.jlpt_new}",
            f"音読み: {', '.join(kanji.readings_on)}",
            f"訓読み: {', '.join(kanji.readings_kun)}",
        ]
        if include_meanings:
            info.append(f"意味: {', '.join(kanji.meanings)}")

        if sample_sentence_count > 0:
            sentences = self.get_sample_sentences(kanji, sample_sentence_count)
            info.append(f"例文: {', '.join(sentences)}")

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