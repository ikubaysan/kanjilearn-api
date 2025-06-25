import os
import json
import logging
from typing import Optional, List
import random
from modules.Kanji import Kanji

logger = logging.getLogger(__name__)

class KanjiCollection:
    def __init__(self, sample_sentences_dir: str):
        self.n1, self.n2, self.n3, self.n4, self.n5 = [], [], [], [], []
        self.levels = {
            1: self.n1,
            2: self.n2,
            3: self.n3,
            4: self.n4,
            5: self.n5
        }
        self.sample_sentences_dir = sample_sentences_dir

    def add_kanji(self, kanji: Kanji, require_sample_sentences: bool = True):
        jlpt_new = kanji.jlpt_new
        if jlpt_new is None:
            # This is a kanji that is not part of the JLPT levels - skip
            return

        # Try to load sample sentences if directory is given
        level_str = f"N{jlpt_new}"
        sentence_file = os.path.join(self.sample_sentences_dir, level_str, f"{kanji.character}.json")
        if os.path.exists(sentence_file):
            try:
                with open(sentence_file, "r", encoding="utf-8") as f:
                    kanji.sample_sentences = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sample sentences for {kanji.character} from {sentence_file}: {e}")
                if require_sample_sentences:
                    return
        else:
            logger.warning(f"No sample sentence file found for {kanji.character}. Expected at: {sentence_file}")
            if require_sample_sentences:
                return

        getattr(self, f"n{jlpt_new}").append(kanji)

    def get_random_kanji(self, jlpt_levels: List[int]) -> Optional[Kanji]:
        kanji_pool = []
        for level in jlpt_levels:
            kanji_pool.extend(getattr(self, f'n{level}', []))
        return random.choice(kanji_pool) if kanji_pool else None