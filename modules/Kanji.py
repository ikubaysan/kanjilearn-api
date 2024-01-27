from typing import List, Optional

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

    def get_example_sentences_prompt(self, count: int) -> Optional[str]:

        if count <= 0:
            return None

        prompt = f"漢字: {self.character}; 意味: {self.meanings}; 音読み: {self.readings_on}; 訓読み: {self.readings_kun};"

        prompt += f"""
        Please generate a json array of dictionaries with keys "sentence", "sentence_furigana", and "meaning". 
        Make up to {count} dictionaries; each is a sample sentence containing the kanji '{self.character}'. 
        For "sentence", write a sentence in Japanese. For "sentence_furigana", write the sentence again, 
        but after each kanji write its kana in 【】 - for example, '彼は外国に行くのが好きです。' becomes '彼【かれ】は外国【がいこく】に行【い】くのが好【す】きです。'. For "meaning", translate the sentence. 
        Include only the json array in the response, no or other words and no comments; I'll be taking your raw response and parsing it in code.
        """

        return prompt