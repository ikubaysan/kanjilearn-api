from modules.Kanji import Kanji
from typing import List, Optional
import random

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