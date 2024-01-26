from modules.Config import Config
from modules.OpenAIAPIClient import OpenAIAPIClient
from modules.Kanji import Kanji
import os
import pytest
import json

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def api_client():
    config = Config(os.path.join(base_dir, 'config.ini'))
    return OpenAIAPIClient(base_url=config.base_url, path=config.path, api_key=config.api_key, model=config.model, max_response_tokens=config.max_response_tokens, temperature=config.temperature)

@pytest.fixture
def sample_kanji():
    kanji_data = {
        "strokes": 8,
        "grade": 2,
        "freq": 3,
        "jlpt_old": 4,
        "jlpt_new": 5,
        "meanings": ["Country"],
        "readings_on": ["こく"],
        "readings_kun": ["くに"],
        "wk_level": 6,
        "wk_meanings": ["Country"],
        "wk_readings_on": ["こく"],
        "wk_readings_kun": ["!くに"],
        "wk_radicals": ["Mouth","King","Drop"]
    }

    return Kanji(character="国", data=kanji_data)

def test_APIClient_send_prompt_english(api_client: OpenAIAPIClient):
    response = api_client.send_prompt(prompt="What is 9 plus 10?")
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_APIClient_send_prompt_japanese(api_client: OpenAIAPIClient):
    response = api_client.send_prompt(prompt="9たす10は何ですか？")
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0



def test_APIClient_send_prompt_japanese_examples(api_client: OpenAIAPIClient, sample_kanji: Kanji):
    prompt = sample_kanji.get_example_sentences_prompt(count=5)

    # this could fail
    response = api_client.send_prompt(prompt=prompt)
    assert response is not None
    assert isinstance(response, str)

    response.replace('\n', ' ')
    try:
        response_list_of_dicts = json.loads(response)
    except Exception as e:
        raise Exception(f"Response is not valid JSON: '{response}'. Error: {e}")

    assert isinstance(response_list_of_dicts, list)
    assert len(response_list_of_dicts) > 0