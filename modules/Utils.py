from typing import List
from modules.SampleSentence import SampleSentence
from modules.Kanji import Kanji

def pad_and_join(strings: List[str], pad_length: int) -> str:
    """
    Pads each string in the list with spaces on the right to the specified pad_length if necessary,
    then joins them into a single string.

    Each string in strings will be up to pad_length characters

    Args:
        strings: List of strings to pad and join.
        pad_length: Number of characters to pad each string to.

    Returns:
        A single string with each padded substring concatenated.
    """
    padded_strings = [(s[:pad_length]).ljust(pad_length) for s in strings]
    return ''.join(padded_strings)



def format_kanji_info(sample_sentences: List[SampleSentence], kanji: Kanji, include_meanings: bool = True) -> str:
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





if __name__ == "__main__":
    strings = [
        "http://localhost:5733/audio/N3/%E6%8A%B1/%E6%8A%B1_25.ogg",
        "http://localhost:5733/audio/N3/%E6%8A%B1/%E6%8A%B1_43.ogg",
        "http://localhost:5733/audio/N3/%E9%81%B8/%E9%81%B8_13.ogg"
    ]
    result = pad_and_join(strings, 250)
    print(result)
    pass