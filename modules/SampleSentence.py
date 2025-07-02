class SampleSentence:
    def __init__(self, sentence: str, sentence_furigana: str, meaning: str):
        self.sentence = sentence
        self.sentence_furigana = sentence_furigana
        self.meaning = meaning
        self.lines_with_meaning = f"{self.sentence}\n{self.sentence_furigana}\n{self.meaning}\n"
        self.lines_without_meaning = f"{self.sentence}\n{self.sentence_furigana}\n"
