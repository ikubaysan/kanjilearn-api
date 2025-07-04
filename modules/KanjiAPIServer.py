import random
from typing import List, Union
from flask import Flask, Response
from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection
from modules.AudioGenerator import AudioGenerator
import logging
from modules.SampleSentence import SampleSentence
import os
from flask import send_from_directory
from modules.Utils import *

logger = logging.getLogger(__name__)


class KanjiAPIServer:
    def __init__(self, collection: KanjiCollection, public_hostname: str, port:int, max_chars_per_audio_url: int, sample_sentence_count: int = 3):
        self.collection = collection

        for level in collection.levels:
            logger.info(f"Loaded {len(getattr(collection, f'n{level}'))} kanji for JLPT N{level}.")

        self.app = Flask(__name__)
        self.app.add_url_rule('/random_kanji/', 'get_kanji', self.get_kanji, methods=['GET'], defaults={'levels': ''})
        self.app.add_url_rule('/random_kanji/<levels>', 'get_kanji', self.get_kanji, methods=['GET'])
        self.app.add_url_rule('/quiz/', 'quiz_kanji', self.get_quiz_kanji, methods=['GET'], defaults={'levels': ''})
        self.app.add_url_rule('/quiz/<levels>', 'quiz_kanji', self.get_quiz_kanji, methods=['GET'])

        # Audio files will be served at
        # http://<hostname>:<port>/audio/<JLPT_LEVEL>/<KANJI>/<KANJI>_<IDX>.ogg
        # Eg http://localhost:5000/audio/N3/選/選_13.ogg

        self.app.add_url_rule(
            '/audio/<path:filename>',
            'serve_audio',
            self.serve_audio,
            methods=['GET']
        )

        self.max_chars_per_audio_url = max_chars_per_audio_url
        self.sample_sentence_count = sample_sentence_count
        self.public_hostname = public_hostname
        self.port = port

        self.audio_generator = AudioGenerator(
            kanji_json_path='',  # Not needed here
            categories_dir=collection.categories_dir,
            convert_to_ogg=True
        )

    def serve_audio(self, filename):
        audio_dir = os.path.abspath(self.collection.categories_dir)
        return send_from_directory(audio_dir, filename, as_attachment=False)

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
        sample_sentences, audio_urls = self.get_sample_sentences(kanji)

        logger.info(f"Audio URLs for {kanji.character}: {audio_urls}")

        if kanji:
            response = self.format_kanji_info(sample_sentences=sample_sentences, kanji=kanji, include_meanings=True)
            response = f"{pad_and_join(strings=audio_urls, pad_length=self.max_chars_per_audio_url)}{response}"
            return Response(response, mimetype='text/plain')
        else:
            return Response("No kanji found for the specified JLPT levels.", status=404)

    def get_quiz_kanji(self, levels: str = '') -> Response:
        if levels:
            try:
                jlpt_levels = [int(level) for level in levels.split(',') if level.strip()]
            except ValueError:
                return Response("Invalid JLPT level format.", status=400)
        else:
            jlpt_levels = [1, 2, 3, 4, 5]

        kanji_pool = []
        for level in jlpt_levels:
            kanji_pool.extend(getattr(self.collection, f'n{level}', []))

        if len(kanji_pool) < 5:
            return Response("Insufficient kanji data for the quiz. Need at least 5 kanji.", status=404)

        try:
            # Get 5 unique random kanji
            quiz_kanji = random.sample(kanji_pool, 5)
        except ValueError as e:
            # This block may not be necessary since we're already checking the pool size,
            # but it's good practice to handle potential exceptions from random.sample.
            return Response(str(e), status=404)

        kanji = quiz_kanji[0]
        sample_sentences, audio_urls = self.get_sample_sentences(kanji)

        kanji_info_without_meanings = self.format_kanji_info(sample_sentences=sample_sentences,
                                                             kanji=kanji,
                                                             include_meanings=False)
        kanji_info_with_meanings = self.format_kanji_info(sample_sentences=sample_sentences,
                                                          kanji=kanji,
                                                          include_meanings=True)

        meanings = [kanji.meanings for kanji in quiz_kanji]
        random.shuffle(meanings)
        correct_answer_index = meanings.index(kanji.meanings)

        response = f"{kanji_info_without_meanings}@{kanji_info_with_meanings}@{'@'.join([', '.join(m) for m in meanings])}@{correct_answer_index}"
        return Response(response, mimetype='text/plain')

    def get_public_audio_url(self, local_file_path: str) -> str:
        """
        Converts a local audio file path returned by generate_audio_for_kanji
        to its corresponding public URL based on self.public_hostname.

        Example:
        local_file_path:
            C:/Users/MyUsername/.../kanji_data/categories/N3/選/選_13.ogg
        returns:
            http://<public_hostname>/audio/N3/選/選_13.ogg
        """
        try:
            relative_path = os.path.relpath(
                local_file_path,
                os.path.abspath(self.collection.categories_dir)
            )
            # Ensure URL uses forward slashes even on Windows
            relative_path_url = relative_path.replace(os.path.sep, '/')
            public_url = f"{self.public_hostname}:{self.port}/audio/{relative_path_url}"

            # Add http:// to the start of public_url if it's not already there
            if not public_url.startswith("http://") and not public_url.startswith("https://"):
                public_url = f"http://{public_url}"

            return public_url
        except Exception as e:
            logger.error(f"Error generating public URL for {local_file_path}: {e}")
            return ""

    def get_sample_sentences(self, kanji: Kanji) -> Union[List[SampleSentence], List[str]]:
        count_of_sample_sentences = len(kanji.sample_sentences)

        if count_of_sample_sentences == 0:
            raise ValueError(f"get_sample_sentences() - No sample sentences available for kanji: {kanji.character}")

        # Select <sample_sentence_count> unique random indices
        sample_sentence_indices = random.sample(
            range(count_of_sample_sentences),
            min(self.sample_sentence_count, count_of_sample_sentences)
        )

        # Generate audio files if missing and get their local paths
        generated_files = self.audio_generator.generate_audio_for_kanji(
            kanji,
            sample_sentence_indices=sample_sentence_indices
        )

        # Log public URLs for each generated file
        audio_urls = []
        for local_file in generated_files:
            public_url = self.get_public_audio_url(local_file)
            if public_url:
                #    logger.info(f"Public URL available: {public_url}")
                audio_urls.append(public_url)
            else:
                audio_urls.append("")

        # Return the selected sample sentences for further formatting
        sample_sentences = [kanji.sample_sentences[i] for i in sample_sentence_indices]
        return sample_sentences, audio_urls

    def format_kanji_info(self, sample_sentences: List[SampleSentence], kanji: Kanji, include_meanings: bool = True) -> str:
        info = [
            #f"画数: {kanji.strokes}",
            #f"学年: {kanji.grade}",
            f"{kanji.character} (N{kanji.jlpt_new})",
            f"音読み: {', '.join(kanji.readings_on)}",
            f"訓読み: {', '.join(kanji.readings_kun)}",
        ]
        if include_meanings:
            info.append(f"意味: {', '.join(kanji.meanings)}")

        if len(sample_sentences) > 0:
            if include_meanings:
                sentences = [sample_sentence.lines_with_meaning for sample_sentence in sample_sentences]
            else:
                sentences = [sample_sentence.lines_without_meaning for sample_sentence in sample_sentences]

            sentence_str = '\n'.join(sentences)
            info.append(f"\n{sentence_str}")

        return '\n'.join(info)

