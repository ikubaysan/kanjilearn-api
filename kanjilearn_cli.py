#!/usr/bin/env python3
"""
kanji_quiz_cli.py
A self-contained, offline command-line kanji quiz.
It reads the same data files used by the kanjilearn-api webapp/API
(kanji_data/kanji.json and kanji_data/categories/N{level}/{kanji}/{kanji}.json)
directly off disk. It does NOT talk to the Flask API, does NOT do any
audio generation/playback, and has no dependency on Flask/requests/etc.
This file is fully standalone - it does not import anything from the
`modules` package, so it can be dropped anywhere and run with nothing
but the Python standard library, as long as it can find `kanji_data`.
Usage:
    python kanji_quiz_cli.py
    python kanji_quiz_cli.py --levels 5 4
    python kanji_quiz_cli.py --mode match
    python kanji_quiz_cli.py --data-dir /path/to/kanji_data
Modes:
    choice  - The original mode. You're shown a kanji + sample
              sentences and pick the correct meaning from a list of
              multiple-choice options.
    match   - New mode. You're shown N randomly selected sample
              sentences (in Japanese, with furigana) and a shuffled
              list of their English meanings. You match each sentence
              to its correct meaning.
    If not passed via --mode, you'll be prompted to choose
    interactively (or "choice" is used by default in non-interactive
    contexts).
During the "choice" mode quiz:
    - Press a number key (no Enter needed) to answer.
    - Press 's' to skip the current kanji (no answer recorded, and this
      forces a move to a new kanji even if you haven't answered
      correctly yet).
    - Press 'q' to quit.
    - If you pick a wrong answer, only your first attempt on that
      kanji is recorded for stats purposes - you must then keep
      choosing until you pick the correct meaning before moving on
      (unless you skip to force a new kanji).
    - After answering correctly (or skipping), press Enter or any
      number key (no need to press Enter afterward) to move to the
      next kanji.
During the "match" mode quiz:
    - Each round shows a set of Japanese sample sentences, numbered,
      and a shuffled list of lettered English meanings.
    - For each numbered sentence, press the letter key of the meaning
      you think matches it (no Enter needed).
    - Press 'q' at any point to quit.
    - After all sentences in the round are matched, you'll see which
      ones were correct/incorrect and the right pairings, then press
      Enter (or any key) to move to the next round.
Stats:
    - Overall accuracy (integer %) plus correct/incorrect/total counts
      are tracked for the current session only, separately per mode.
    - In "choice" mode, a separate "unique kanji" accuracy is also
      tracked: for each kanji character, only your MOST RECENT
      first-attempt result counts.
    - Nothing is saved to disk - stats reset every time you run the
      script.
"""
import argparse
import json
import os
import random
import string
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
# --------------------------------------------------------------------------
# Data classes
# --------------------------------------------------------------------------
@dataclass
class SampleSentence:
    sentence: str
    sentence_furigana: str
    meaning: str
@dataclass
class QuizKanji:
    character: str
    jlpt_level: int
    meanings: List[str]
    readings_on: List[str]
    readings_kun: List[str]
    sample_sentences: List[SampleSentence] = field(default_factory=list)
    @property
    def meaning_str(self) -> str:
        return ", ".join(self.meanings)
# --------------------------------------------------------------------------
# Single-keypress input (no Enter required)
# --------------------------------------------------------------------------
def flush_input_buffer() -> None:
    """
    Discards any keypresses that are queued up but not yet read. This
    matters because holding a key down (e.g. to answer a question)
    generates OS-level key-repeat, which can leave extra copies of
    that key sitting in the input buffer. Without flushing, those
    leftover presses get silently consumed by the *next* prompt
    (e.g. immediately "answering" the next kanji with a stale
    keystroke instead of waiting for a fresh one).
    """
    try:
        import msvcrt  # Windows
        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        import termios
        try:
            fd = sys.stdin.fileno()
            termios.tcflush(fd, termios.TCIFLUSH)
        except Exception:
            pass
def get_keypress() -> str:
    """
    Reads a single keypress from the terminal without requiring Enter,
    and without echoing it (we echo manually where needed). Works on
    Windows (msvcrt) and POSIX (termios/tty).
    """
    try:
        import msvcrt  # Windows
        ch = msvcrt.getch()
        # Special keys (arrows, F-keys) come through as a two-byte
        # sequence starting with b'\x00' or b'\xe0'. Swallow the
        # follow-up byte so it doesn't get misread as a real answer.
        if ch in (b"\x00", b"\xe0"):
            msvcrt.getch()
            return ""
        try:
            return ch.decode("utf-8", errors="ignore").lower()
        except Exception:
            return ""
    except ImportError:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch.lower()
# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_kanji_pool(data_dir: str) -> Dict[int, List[QuizKanji]]:
    """
    Loads kanji.json + per-kanji sample sentence files from disk and
    returns a dict of {jlpt_level: [QuizKanji, ...]}.
    Only kanji that have at least one valid, loadable sample sentence
    file are included, matching the behavior the API uses when serving
    quiz data (require_sample_sentences=True).
    """
    kanji_json_path = os.path.join(data_dir, "kanji.json")
    categories_dir = os.path.join(data_dir, "categories")
    if not os.path.exists(kanji_json_path):
        print(f"ERROR: Could not find kanji.json at: {kanji_json_path}")
        sys.exit(1)
    with open(kanji_json_path, "r", encoding="utf-8") as f:
        raw_kanji_data = json.load(f)
    pool: Dict[int, List[QuizKanji]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    for character, data in raw_kanji_data.items():
        jlpt_new = data.get("jlpt_new")
        if jlpt_new is None or jlpt_new not in pool:
            # Not part of the N5-N1 JLPT levels - skip, same as KanjiCollection.
            continue
        sentence_file = os.path.join(
            categories_dir, f"N{jlpt_new}", character, f"{character}.json"
        )
        if not os.path.exists(sentence_file):
            continue
        try:
            with open(sentence_file, "r", encoding="utf-8") as sf:
                sentence_data = json.load(sf)
        except Exception as e:
            print(f"WARNING: Failed to load sentences for {character}: {e}")
            continue
        sample_sentences = []
        for entry in sentence_data:
            sentence = entry.get("sentence")
            sentence_furigana = entry.get("sentence_furigana")
            meaning = entry.get("meaning")
            if sentence and sentence_furigana and meaning:
                sample_sentences.append(
                    SampleSentence(sentence, sentence_furigana, meaning)
                )
        if not sample_sentences:
            continue
        kanji = QuizKanji(
            character=character,
            jlpt_level=jlpt_new,
            meanings=data.get("meanings", []),
            readings_on=data.get("readings_on", []),
            readings_kun=data.get("readings_kun", []),
            sample_sentences=sample_sentences,
        )
        pool[jlpt_new].append(kanji)
    return pool
# --------------------------------------------------------------------------
# Shared base: level filtering + kanji list building
# --------------------------------------------------------------------------
class BaseQuiz:
    def __init__(self, pool: Dict[int, List[QuizKanji]], levels: List[int]):
        self.levels = sorted(levels)
        self.kanji_list: List[QuizKanji] = []
        for level in self.levels:
            self.kanji_list.extend(pool.get(level, []))
        if not self.kanji_list:
            print("ERROR: No kanji with sample sentences found for the "
                  "selected level(s).")
            sys.exit(1)
    def print_intro(self, title: str, extra_lines: List[str]):
        print(f"\n=== {title} ===")
        print(f"Levels in play: {', '.join('N' + str(l) for l in self.levels)}")
        print(f"Kanji available: {len(self.kanji_list)}")
        for line in extra_lines:
            print(line)
        print()
# --------------------------------------------------------------------------
# Mode 1: Multiple-choice quiz (kanji -> meaning)
# --------------------------------------------------------------------------
class KanjiChoiceQuiz(BaseQuiz):
    def __init__(self, pool: Dict[int, List[QuizKanji]], levels: List[int],
                 sentence_count: int = 3, choice_count: int = 4):
        super().__init__(pool, levels)
        self.sentence_count = sentence_count
        self.choice_count = choice_count
        self.stats = {"total_correct": 0, "total_incorrect": 0, "kanji_results": {}}
        # All distinct meaning strings available in the selected pool,
        # used to build multiple-choice distractors.
        self.all_meaning_strings = list({k.meaning_str for k in self.kanji_list})
    def pick_random_kanji(self) -> QuizKanji:
        return random.choice(self.kanji_list)
    def pick_sample_sentences(self, kanji: QuizKanji) -> List[SampleSentence]:
        n = min(self.sentence_count, len(kanji.sample_sentences))
        return random.sample(kanji.sample_sentences, n)
    def build_choices(self, correct_kanji: QuizKanji) -> List[str]:
        correct = correct_kanji.meaning_str
        distractor_pool = [m for m in self.all_meaning_strings if m != correct]
        n_distractors = min(self.choice_count - 1, len(distractor_pool))
        distractors = random.sample(distractor_pool, n_distractors)
        choices = distractors + [correct]
        random.shuffle(choices)
        return choices
    def run(self):
        self.print_intro(
            "Kanji Quiz - Multiple Choice",
            [
                "Commands: press a number key to answer, 's' to skip "
                "(forces a new kanji), 'q' to quit.",
                "If you answer wrong, you'll need to pick the correct "
                "meaning before moving on - unless you skip.",
            ],
        )
        self.print_stats()
        print()
        while True:
            kanji = self.pick_random_kanji()
            result = self.run_single_round(kanji)
            if result == "quit":
                print("\nThanks for studying! さようなら 👋")
                return
    def run_single_round(self, kanji: QuizKanji) -> str:
        sentences = self.pick_sample_sentences(kanji)
        choices = self.build_choices(kanji)
        correct = kanji.meaning_str
        self.print_kanji_block(kanji, sentences)
        self.print_choices(choices)
        first_attempt = True
        skipped = False
        while True:
            answer_index = self.prompt_for_answer(len(choices))
            if answer_index == "quit":
                return "quit"
            if answer_index == "skip":
                print(f"\nSkipped. ({kanji.character} means: {correct})\n")
                skipped = True
                break
            chosen = choices[answer_index]
            is_correct = (chosen == correct)
            if first_attempt:
                self.record_result(kanji.character, is_correct)
                first_attempt = False
            if is_correct:
                print("\n✅ Correct!")
                break
            print(f"\n❌ Incorrect. You chose: {chosen}")
            print(f"   The correct meaning was: {correct}")
            print("Try again - pick the correct meaning to continue "
                  "(or 's' to skip to a new kanji).\n")
            flush_input_buffer()
            self.print_choices(choices)
        if not skipped:
            self.print_stats()
        self.print_sentence_meanings(sentences)
        self.prompt_for_next()
        print("-" * 60)
        return "continue"
    # ---- stats helpers ----
    def record_result(self, character: str, is_correct: bool) -> None:
        if is_correct:
            self.stats["total_correct"] += 1
        else:
            self.stats["total_incorrect"] += 1
        # Only the most recent first-attempt result for a given kanji
        # counts toward the "unique kanji" accuracy metric.
        self.stats["kanji_results"][character] = is_correct
    def print_stats(self) -> None:
        total_correct = self.stats["total_correct"]
        total_incorrect = self.stats["total_incorrect"]
        total = total_correct + total_incorrect
        overall_acc = round(100 * total_correct / total) if total else 0
        kanji_results = self.stats["kanji_results"]
        unique_total = len(kanji_results)
        unique_correct = sum(1 for v in kanji_results.values() if v)
        unique_acc = round(100 * unique_correct / unique_total) if unique_total else 0
        print(f"📊 Overall accuracy: {overall_acc}% "
              f"({total_correct} correct, {total_incorrect} incorrect, {total} total)")
        print(f"📊 Unique kanji accuracy: {unique_acc}% "
              f"({unique_correct}/{unique_total} unique kanji, latest result only)")
    # ---- display helpers ----
    def print_kanji_block(self, kanji: QuizKanji, sentences: List[SampleSentence]):
        print(f"\n{kanji.character} (N{kanji.jlpt_level})")
        print(f"onyomi: {', '.join(kanji.readings_on) if kanji.readings_on else '-'}")
        print(f"kunyomi: {', '.join(kanji.readings_kun) if kanji.readings_kun else '-'}")
        print()
        for s in sentences:
            print(s.sentence)
            print(s.sentence_furigana)
        print()
    def print_choices(self, choices: List[str]):
        print("Select the meaning:")
        for i, choice in enumerate(choices, start=1):
            print(f"  {i}. {choice}")
    def print_sentence_meanings(self, sentences: List[SampleSentence]):
        print("\nSentence meanings:")
        for s in sentences:
            print(f"  {s.sentence}")
            print(f"    -> {s.meaning}")
    def prompt_for_answer(self, num_choices: int):
        flush_input_buffer()
        print(f"\nYour answer (1-{num_choices}, 's' to skip, 'q' to quit): ",
              end="", flush=True)
        while True:
            ch = get_keypress()
            if ch == "q":
                print("q")
                return "quit"
            if ch == "s":
                print("s")
                return "skip"
            if ch.isdigit() and 1 <= int(ch) <= num_choices:
                print(ch)
                return int(ch) - 1
            # Ignore any other keypress (no Enter needed, no echo, just
            # keep waiting for a valid key).
    def prompt_for_next(self):
        flush_input_buffer()
        print("\nPress Enter, or any number key, for next kanji ('q' to quit): ",
              end="", flush=True)
        while True:
            ch = get_keypress()
            if ch in ("\r", "\n"):
                print()
                return
            if ch == "q":
                print("q")
                print("\nThanks for studying! さようなら 👋")
                sys.exit(0)
            if ch.isdigit():
                print(ch)
                return
            # Ignore any other keypress and keep waiting for a valid one.
# --------------------------------------------------------------------------
# Mode 2: Sentence matching quiz (Japanese sentence -> English meaning)
# --------------------------------------------------------------------------
class SentenceMatchQuiz(BaseQuiz):
    def __init__(self, pool: Dict[int, List[QuizKanji]], levels: List[int],
                 match_count: int = 5):
        super().__init__(pool, levels)
        self.match_count = match_count
        # Flatten every (kanji, sentence) pair across the selected
        # levels so a round can draw sentences from different kanji.
        self.all_sentences: List[Tuple[QuizKanji, SampleSentence]] = []
        for k in self.kanji_list:
            for s in k.sample_sentences:
                self.all_sentences.append((k, s))
        if len(self.all_sentences) < 2:
            print("ERROR: Not enough sample sentences found for the "
                  "selected level(s) to run matching mode.")
            sys.exit(1)
        # Round size can't exceed however many sentences we actually have.
        self.round_size = min(self.match_count, len(self.all_sentences))
        self.stats = {"total_correct": 0, "total_incorrect": 0, "rounds": 0}
    def run(self):
        self.print_intro(
            "Kanji Quiz - Sentence Matching",
            [
                f"Each round: match {self.round_size} Japanese sentences to "
                "their English meanings.",
                "Commands: press the letter key of your match for each "
                "sentence, 'q' to quit.",
            ],
        )
        self.print_stats()
        print()
        while True:
            result = self.run_single_round()
            if result == "quit":
                print("\nThanks for studying! さようなら 👋")
                return
    def run_single_round(self) -> str:
        picks = random.sample(self.all_sentences, self.round_size)
        sentences = [s for _, s in picks]
        letters = list(string.ascii_uppercase[: self.round_size])
        # Shuffle the order the meanings are displayed in (as numbered
        # options 1..N), independent of sentence order (lettered
        # A..N), so the numbers don't just line up 1:1 with letters.
        shuffled_indices = list(range(self.round_size))
        random.shuffle(shuffled_indices)
        # number (1-based) -> index into `sentences` whose meaning is
        # shown at that number.
        number_to_sentence_index = {
            pos + 1: shuffled_indices[pos] for pos in range(self.round_size)
        }
        self.print_sentences(sentences, letters)
        self.print_meaning_options(sentences, shuffled_indices)
        user_matches: Dict[int, int] = {}  # sentence index -> chosen number
        for i in range(self.round_size):
            flush_input_buffer()
            print(f"\nSentence {letters[i]}: match to which meaning? "
                  f"(1-{self.round_size}, 'q' to quit): ", end="", flush=True)
            choice = self.prompt_for_number(self.round_size)
            if choice == "quit":
                return "quit"
            print(choice)
            user_matches[i] = choice
        self.score_round(sentences, letters, user_matches, number_to_sentence_index)
        self.print_stats()
        self.prompt_for_next()
        print("-" * 60)
        return "continue"
    def score_round(self, sentences: List[SampleSentence], letters: List[str],
                     user_matches: Dict[int, int],
                     number_to_sentence_index: Dict[int, int]) -> None:
        print("\nResults:")
        round_correct = 0
        for i, sentence in enumerate(sentences):
            chosen_number = user_matches[i]
            chosen_sentence_index = number_to_sentence_index[chosen_number]
            is_correct = (chosen_sentence_index == i)
            self.stats["total_correct" if is_correct else "total_incorrect"] += 1
            if is_correct:
                round_correct += 1
                print(f"  ✅ Sentence {letters[i]}: {chosen_number} - {sentence.meaning}")
            else:
                print(f"  ❌ Sentence {letters[i]}: you picked {chosen_number} "
                      f"({sentences[chosen_sentence_index].meaning})")
                print(f"      correct meaning: {sentence.meaning}")
        self.stats["rounds"] += 1
        print(f"\nRound score: {round_correct}/{self.round_size}")
    # ---- stats helpers ----
    def print_stats(self) -> None:
        total_correct = self.stats["total_correct"]
        total_incorrect = self.stats["total_incorrect"]
        total = total_correct + total_incorrect
        overall_acc = round(100 * total_correct / total) if total else 0
        print(f"📊 Match accuracy: {overall_acc}% "
              f"({total_correct} correct, {total_incorrect} incorrect, "
              f"{total} matches across {self.stats['rounds']} rounds)")
    # ---- display helpers ----
    def print_sentences(self, sentences: List[SampleSentence], letters: List[str]):
        print("\nJapanese sentences:")
        for letter, s in zip(letters, sentences):
            print(f"\n  {letter}. {s.sentence}")
            print(f"     {s.sentence_furigana}")
    def print_meaning_options(self, sentences: List[SampleSentence],
                               shuffled_indices: List[int]):
        print("\nEnglish meanings:")
        for pos, sentence_index in enumerate(shuffled_indices):
            print(f"  {pos + 1}. {sentences[sentence_index].meaning}")
    def prompt_for_number(self, num_choices: int):
        while True:
            ch = get_keypress()
            if ch == "q":
                return "quit"
            if ch.isdigit() and 1 <= int(ch) <= num_choices:
                return int(ch)
            # Ignore any other keypress and keep waiting for a valid one.
    def prompt_for_next(self):
        flush_input_buffer()
        print("\nPress Enter, or any key, for next round ('q' to quit): ",
              end="", flush=True)
        while True:
            ch = get_keypress()
            if ch in ("\r", "\n"):
                print()
                return
            if ch == "q":
                print("q")
                print("\nThanks for studying! さようなら 👋")
                sys.exit(0)
            if ch:
                print(ch)
                return
# --------------------------------------------------------------------------
# Level / mode selection
# --------------------------------------------------------------------------
def parse_levels_arg(levels_arg: Optional[List[str]]) -> List[int]:
    if not levels_arg:
        return [5, 4, 3, 2, 1]
    parsed = []
    for raw in levels_arg:
        cleaned = raw.strip().upper().replace("N", "")
        if cleaned.isdigit() and int(cleaned) in (1, 2, 3, 4, 5):
            parsed.append(int(cleaned))
        else:
            print(f"WARNING: Ignoring unrecognized level '{raw}'.")
    return sorted(set(parsed)) if parsed else [5, 4, 3, 2, 1]
def prompt_for_levels_interactively() -> List[int]:
    print("Select JLPT level(s) to quiz on.")
    print("Enter one or more of 5 4 3 2 1 separated by spaces or commas.")
    print("Press Enter with no input to include all levels (N5-N1).")
    raw = input("Levels: ").strip()
    if not raw:
        return [5, 4, 3, 2, 1]
    tokens = raw.replace(",", " ").split()
    return parse_levels_arg(tokens)
MODE_CHOICE = "choice"
MODE_MATCH = "match"
VALID_MODES = (MODE_CHOICE, MODE_MATCH)
def parse_mode_arg(mode_arg: Optional[str]) -> str:
    if not mode_arg:
        return MODE_CHOICE
    cleaned = mode_arg.strip().lower()
    if cleaned in VALID_MODES:
        return cleaned
    # A couple of friendly aliases.
    if cleaned in ("mc", "multiple-choice", "multiplechoice"):
        return MODE_CHOICE
    if cleaned in ("matching", "sentence-match", "sentencematch"):
        return MODE_MATCH
    print(f"WARNING: Unrecognized mode '{mode_arg}', defaulting to 'choice'.")
    return MODE_CHOICE
def prompt_for_mode_interactively() -> str:
    print("Select a quiz mode.")
    print("  1. choice - kanji + sample sentences, pick the meaning "
          "(multiple choice)")
    print("  2. match  - match several sample sentences to their "
          "English meanings")
    raw = input("Mode [1/2, Enter for choice]: ").strip().lower()
    if raw in ("2", "match", "matching", "m"):
        return MODE_MATCH
    return MODE_CHOICE
# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Offline CLI Kanji Quiz")
    parser.add_argument(
        "--mode", choices=list(VALID_MODES), default=None,
        help="Quiz mode: 'choice' (kanji -> meaning, multiple choice) or "
             "'match' (match sample sentences to their English meanings). "
             "If omitted, you'll be prompted (or 'choice' is used in "
             "non-interactive contexts)."
    )
    parser.add_argument(
        "--levels", nargs="+", default=None,
        help="JLPT levels to quiz on, e.g. --levels 5 4 3. "
             "If omitted, you'll be prompted (or all levels are used "
             "in non-interactive contexts)."
    )
    parser.add_argument(
        "--data-dir", default=None,
        help="Path to the kanji_data directory "
             "(default: ./kanji_data relative to this script)."
    )
    parser.add_argument(
        "--sentence-count", type=int, default=3,
        help="[choice mode] Number of sample sentences to show per kanji "
             "(default: 3)."
    )
    parser.add_argument(
        "--choice-count", type=int, default=4,
        help="[choice mode] Number of multiple-choice meaning options "
             "(default: 4)."
    )
    parser.add_argument(
        "--match-count", type=int, default=5,
        help="[match mode] Number of sentences to match per round "
             "(default: 5)."
    )
    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = args.data_dir or os.path.join(base_dir, "kanji_data")
    interactive_stdin = True
    try:
        sys.stdin.fileno()
    except Exception:
        interactive_stdin = False
    if args.mode is not None:
        mode = parse_mode_arg(args.mode)
    else:
        try:
            mode = prompt_for_mode_interactively()
        except EOFError:
            mode = MODE_CHOICE
    if args.levels is not None:
        levels = parse_levels_arg(args.levels)
    else:
        try:
            levels = prompt_for_levels_interactively()
        except EOFError:
            # No interactive stdin available - default to all levels.
            levels = [5, 4, 3, 2, 1]
    pool = load_kanji_pool(data_dir)
    if mode == MODE_MATCH:
        quiz = SentenceMatchQuiz(
            pool=pool,
            levels=levels,
            match_count=args.match_count,
        )
    else:
        quiz = KanjiChoiceQuiz(
            pool=pool,
            levels=levels,
            sentence_count=args.sentence_count,
            choice_count=args.choice_count,
        )
    try:
        quiz.run()
    except KeyboardInterrupt:
        print("\n\nQuiz interrupted. さようなら 👋")
if __name__ == "__main__":
    main()