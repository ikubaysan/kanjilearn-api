from typing import List

def pad_and_join(strings: List[str], pad_length: int) -> str:
    """
    Pads each string in the list with spaces on the right to the specified pad_length if necessary,
    then joins them into a single string.

    Args:
        strings: List of strings to pad and join.
        pad_length: Number of characters to pad each string to.

    Returns:
        A single string with each padded substring concatenated.
    """
    padded_strings = [s.ljust(pad_length) for s in strings]
    return ''.join(padded_strings)



if __name__ == "__main__":
    strings = [
        "http://localhost:5733/audio/N3/%E6%8A%B1/%E6%8A%B1_25.ogg",
        "http://localhost:5733/audio/N3/%E6%8A%B1/%E6%8A%B1_43.ogg",
        "http://localhost:5733/audio/N3/%E9%81%B8/%E9%81%B8_13.ogg"
    ]
    result = pad_and_join(strings, 250)
    print(result)
    pass