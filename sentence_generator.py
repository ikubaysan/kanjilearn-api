from modules.SentenceGenerator import SentenceGenerator
import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Optional CLI args; if not provided, will remain None
    parser.add_argument("--max_attempts_per_kanji", type=int, help="Max attempts per kanji")
    parser.add_argument("--sleep_seconds", type=int, help="Seconds to sleep between requests")
    parser.add_argument("--sentence_count", type=int, help="Number of sentences per kanji")
    parser.add_argument("--skip_existing", action="store_true", help="Skip existing kanji")
    parser.add_argument("--randomize-order", action="store_true", help="Randomize order of handling kanji")


    # Example usage:
    # python your_script.py --max_attempts_per_kanji 3 --sleep_seconds 2 --sentence_count 50 --skip_existing

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    kanji_json = os.path.join(base_dir, 'kanji_data', 'kanji.json')
    config_ini = os.path.join(base_dir, 'config.ini')
    categories_directory = os.path.join(base_dir, 'kanji_data', "categories")

    # Build kwargs only for args that were actually provided
    generator_kwargs = {}
    if args.max_attempts_per_kanji is not None:
        generator_kwargs["max_attempts_per_kanji"] = args.max_attempts_per_kanji
    if args.sleep_seconds is not None:
        generator_kwargs["sleep_seconds"] = args.sleep_seconds
    if args.sentence_count is not None:
        generator_kwargs["sentence_count"] = args.sentence_count
    if args.skip_existing:
        generator_kwargs["skip_existing"] = True
    if args.randomize_order:
        generator_kwargs["randomize_order"] = True

    generator = SentenceGenerator(
        kanji_json_path=kanji_json,
        categories_dir=categories_directory,
        config_path=config_ini,
        **generator_kwargs
    )
    generator.generate_for_all()
