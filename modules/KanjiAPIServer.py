import random
from typing import List, Optional
from flask import Flask, Response
from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection
from modules.OpenAIAPIClient import OpenAIAPIClient
import json

class KanjiAPIServer:
    def __init__(self, collection: KanjiCollection, openai_api_client: OpenAIAPIClient = None, sample_sentence_count: int = 3):
        self.collection = collection
        self.app = Flask(__name__)
        self.app.add_url_rule('/random_kanji/', 'get_kanji', self.get_kanji, methods=['GET'], defaults={'levels': ''})
        self.app.add_url_rule('/random_kanji/<levels>', 'get_kanji', self.get_kanji, methods=['GET'])
        self.app.add_url_rule('/quiz/', 'quiz_kanji', self.quiz_kanji, methods=['GET'], defaults={'levels': ''})
        self.app.add_url_rule('/quiz/<levels>', 'quiz_kanji', self.quiz_kanji, methods=['GET'])
        self.sample_sentence_count = sample_sentence_count
        self.openai_api_client = openai_api_client

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
            response = f"{self.format_kanji_info(kanji, include_meanings=True, sample_sentence_count=self.sample_sentence_count)}"
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

        response = f"{first_kanji_info}@{'@'.join([', '.join(m) for m in meanings])}@{correct_answer_index}"
        return Response(response, mimetype='text/plain')


    def get_sample_sentences(self, kanji: Kanji) -> List[str]:
        lines = []

        if self.openai_api_client is None:
            return lines

        prompt = kanji.get_example_sentences_prompt(self.sample_sentence_count)
        if prompt is None:
            return lines

        try:
            response = self.openai_api_client.send_prompt(prompt=prompt)
            response_list_of_dicts = json.loads(response)
            #response_list_of_dicts = [{'sentence': '日本は美しい国です。', 'sentence_furigana': 'にほんは(び)しい(くに)です。', 'meaning': 'Japan is a beautiful country.'}, {'sentence': '私はその国の文化に興味があります。', 'sentence_furigana': 'わたしはその(くに)の(ぶんか)に(きょうみ)があります。', 'meaning': 'I am interested in the culture of that country.'}, {'sentence': '彼は外国に行くのが好きです。', 'sentence_furigana': 'かれは(がいこく)に(い)くのが(す)きです。', 'meaning': 'He likes to go to foreign countries.'}]
            for entry in response_list_of_dicts:
                sentence = entry['sentence']
                furigana = entry['sentence_furigana']
                meaning = entry['meaning']
                lines.append(f"{sentence}\n{furigana}\n{meaning}\n")
        except Exception as e:
            print(f"Failed to send prompt to OpenAI API and parse response content: {e}.")

        return lines

    def format_kanji_info(self, kanji: Kanji, include_meanings: bool = True, sample_sentence_count: int = 0) -> str:
        info = [
            #f"画数: {kanji.strokes}",
            #f"学年: {kanji.grade}",
            f"{kanji.character} (N{kanji.jlpt_new})",
            f"音読み: {', '.join(kanji.readings_on)}",
            f"訓読み: {', '.join(kanji.readings_kun)}",
        ]
        if include_meanings:
            info.append(f"意味: {', '.join(kanji.meanings)}")

        if sample_sentence_count > 0:
            sentences = self.get_sample_sentences(kanji)
            sentence_str = '\n'.join(sentences)
            #info.append(f"例文:\n{sentence_str}")
            info.append(f"\n{sentence_str}")

        return '\n'.join(info)

