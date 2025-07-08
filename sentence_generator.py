from modules.SentenceGenerator import SentenceGenerator
import os
import argparse

if __name__ == "__main__":

    # Example usage:
    # python sentence_generator.py --max_attempts_per_kanji 3 --sleep_seconds 2 --sentence_count 50 --skip_existing

    base_dir = os.path.dirname(os.path.abspath(__file__))
    kanji_json = os.path.join(base_dir, 'kanji_data', 'kanji.json')
    config_ini = os.path.join(base_dir, 'config.ini')
    categories_directory = os.path.join(base_dir, 'kanji_data', "categories")

    generator = SentenceGenerator(
        kanji_json_path=kanji_json,
        categories_dir=categories_directory,
        config_path=config_ini,
        max_attempts_per_kanji=5,
        sleep_seconds=1,
        sentence_count=100,
        skip_existing=True
    )
    generator.generate_for_all()