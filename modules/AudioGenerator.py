import os
import json
import logging
from gtts import gTTS

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from modules.Kanji import Kanji
from modules.KanjiCollection import KanjiCollection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self, kanji_json_path: str, categories_dir: str, language: str = 'ja', convert_to_ogg: bool = True):
        self.kanji_json_path = kanji_json_path
        self.categories_dir = categories_dir
        self.language = language
        self.convert_to_ogg = convert_to_ogg

        if self.convert_to_ogg and not PYDUB_AVAILABLE:
            raise ImportError("pydub is required for OGG conversion but is not installed. Install it with 'pip install pydub'.")

    def generate_audio_for_all(self):
        with open(self.kanji_json_path, 'r', encoding='utf-8') as f:
            kanji_data = json.load(f)

        collection = KanjiCollection(categories_dir=self.categories_dir)
        for character, data in kanji_data.items():
            kanji = Kanji(character, data)
            collection.add_kanji(kanji, require_sample_sentences=True)

        all_kanji = collection.n5 + collection.n4 + collection.n3 + collection.n2 + collection.n1

        logger.info(f"Found {len(all_kanji)} kanji with sentence files.")

        for kanji in all_kanji:
            character = kanji.character
            jlpt_level = f"N{kanji.jlpt_new}"
            kanji_dir = os.path.join(self.categories_dir, jlpt_level, character)
            sentence_json = os.path.join(kanji_dir, f"{character}.json")

            if not os.path.exists(sentence_json):
                logger.warning(f"Sentence file missing for {character}: {sentence_json}")
                continue

            with open(sentence_json, 'r', encoding='utf-8') as f:
                sentences = json.load(f)

            logger.info(f"Generating audio for {character} ({len(sentences)} sentences)...")

            for idx, entry in enumerate(sentences):
                text = entry.get('sentence')
                if not text:
                    logger.warning(f"Empty sentence at index {idx} for {character}")
                    continue

                if self.convert_to_ogg:
                    temp_mp3 = os.path.join(kanji_dir, f"{character}_{idx}.mp3")
                    final_audio = os.path.abspath(os.path.join(kanji_dir, f"{character}_{idx}.ogg"))
                else:
                    final_audio = os.path.abspath(os.path.join(kanji_dir, f"{character}_{idx}.mp3"))

                if os.path.exists(final_audio):
                    logger.info(f"Audio already exists: {final_audio}")
                    continue

                try:
                    tts = gTTS(text=text, lang=self.language)
                    if self.convert_to_ogg:
                        tts.save(temp_mp3)
                        audio = AudioSegment.from_mp3(temp_mp3)
                        audio.export(final_audio, format="ogg")
                        os.remove(temp_mp3)
                    else:
                        tts.save(final_audio)

                    logger.info(f"Saved: {final_audio}")
                except Exception as e:
                    logger.error(f"Failed to generate audio for {character} sentence {idx}: {e}")
                    if self.convert_to_ogg and os.path.exists(temp_mp3):
                        os.remove(temp_mp3)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kanji_json = os.path.join(base_dir, '..', 'kanji_data', 'kanji.json')
    categories_directory = os.path.join(base_dir, '..', 'kanji_data', 'categories')

    audio_generator = AudioGenerator(
        kanji_json_path=kanji_json,
        categories_dir=categories_directory,
        language='ja',
        convert_to_ogg=True  # Default True; set to False to output MP3 directly
    )
    audio_generator.generate_audio_for_all()
