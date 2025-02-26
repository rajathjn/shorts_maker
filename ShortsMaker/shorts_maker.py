import json
import logging
import random
from pathlib import Path
from pprint import pformat

import ftfy
import language_tool_python
import praw
import yaml
from praw.models import Submission, Subreddit
from unidecode import unidecode

from .utils import VOICES, generate_audio_transcription, setup_package_logging, tts

# needed for retry decorator
MAX_RETRIES: int = 1
DELAY: int = 0
NOTIFY: bool = False

# Constants
PUNCTUATIONS = [".", ";", ":", "!", "?", '"']
ESCAPE_CHARACTERS = ["\n", "\t", "\r", "  "]
# abbreviation, replacement, padding
ABBREVIATION_TUPLES = [
    ("\n", " ", ""),
    ("\t", " ", ""),
    ("\r", " ", ""),
    ("(", "", ""),
    (")", "", ""),
    ("AITA", "Am I the asshole ", " "),
    ("WIBTA", "Would I be the asshole ", " "),
    ("NTA", "Not the asshole ", " "),
    ("YTA", "You're the Asshole", ""),
    ("YWBTA", "You Would Be the Asshole", ""),
    ("YWNBTA", "You Would Not be the Asshole", ""),
    ("ESH", "Everyone Sucks here", ""),
    ("NAH", "No Assholes here", ""),
    ("INFO", "Not Enough Info", ""),
    ("FIL", "father in law ", " "),
    ("BIL", "brother in law ", " "),
    ("MIL", "mother in law ", " "),
    ("SIL", "sister in law ", " "),
    (" BF ", " boyfriend ", ""),
    (" GF ", " girlfriend ", ""),
    (" bf ", " boyfriend ", ""),
    (" gf ", " girlfriend ", ""),
    ("  ", " ", ""),
]


def abbreviation_replacer(text, abbreviation, replacement, padding=""):
    text = text.replace(abbreviation + padding, replacement)
    text = text.replace(padding + abbreviation, replacement)
    return text


def has_alpha_and_digit(word):
    return any(character.isalpha() for character in word) and any(
        character.isdigit() for character in word
    )


def split_alpha_and_digit(word):
    res = ""
    alpha = False
    digit = False
    for character in word:
        if character.isalpha():
            alpha = True
            if digit:
                res += " "
                digit = False
            res += character
        elif character.isdigit():
            digit = True
            if alpha:
                res += " "
                alpha = False
            res += character
        else:
            res += character
    return res


class ShortsMaker:
    def __init__(self, config_file: Path):
        # check if config file exists
        self.word_transcript = None
        self.line_transcript = None
        self.transcript = None
        self.audio_cfg = None
        self.reddit_post = None
        self.reddit_cfg = None

        self.setup_cfg = Path(config_file) if isinstance(config_file, str) else config_file
        if not self.setup_cfg.exists():
            raise FileNotFoundError(f"File {str(self.setup_cfg)} does not exist")

        if self.setup_cfg.suffix != ".yml":
            raise ValueError(f"File {str(self.setup_cfg)} is not a yaml file")

        # load yaml file
        with open(self.setup_cfg) as f:
            self.cfg = yaml.safe_load(f)

        # check if assets directory exists
        self.assets_dir = Path(self.cfg["assets_dir"])
        if not self.assets_dir.exists():
            raise f"FileNotFound: Assets directory {self.assets_dir} not found"

        # create cache directory
        self.cache_dir = Path(self.cfg["cache_dir"])
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.logging_cfg = {
            "log_file": "shorts_maker.log",
            "logger_name": "ShortsMaker",
            "level": logging.INFO,
            "enable": True,
        }

        if "logging" in self.cfg:
            # override with values in from the setup.yml file
            for key, value in self.cfg["logging"].items():
                self.logging_cfg[key] = value

        self.logger = setup_package_logging(**self.logging_cfg)

        self.retry_cfg = self.cfg["retry"]
        if not self.retry_cfg["enable"]:
            self.retry_cfg["max_retries"] = 1
            self.retry_cfg["delay"] = 0
        global MAX_RETRIES
        global DELAY
        global NOTIFY
        MAX_RETRIES = self.retry_cfg["max_retries"]
        DELAY = self.retry_cfg["delay"]
        NOTIFY = self.retry_cfg["notify"]

    # @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def get_reddit_post(self) -> str:
        self.reddit_cfg = self.cfg["reddit_praw"]
        self.reddit_post = self.cfg["reddit_post_getter"]

        self.logger.info("Getting Reddit post")
        reddit: praw.Reddit = praw.Reddit(
            client_id=self.reddit_cfg["client_id"],
            client_secret=self.reddit_cfg["client_secret"],
            user_agent=self.reddit_cfg["user_agent"],
            # username=self.reddit_cfg["username"],
            # password=self.reddit_cfg["password"]
        )
        self.logger.info(f"Is reddit readonly: {reddit.read_only}")

        subreddit: Subreddit = reddit.subreddit(self.reddit_post["subreddit_name"])
        self.logger.info(f"Subreddit title: {subreddit.title}")
        self.logger.info(f"Subreddit display name: {subreddit.display_name}")

        # Get random submission
        submission: Submission = random.choice(
            [
                submission
                for submission in subreddit.top(time_filter="month", limit=random.randint(3, 3))
            ]
        )
        self.logger.info(f"Submission Url: {submission.url}")
        self.logger.info(f"Submission title: {submission.title}")

        data = dict()
        for key, value in vars(submission).items():
            data[key] = str(value)

        # Save the submission to a json file
        with open(self.cache_dir / self.reddit_post["record_file_json"], "w") as record_file:
            # noinspection PyTypeChecker
            json.dump(data, record_file, indent=4, skipkeys=True, sort_keys=True)
        self.logger.info(
            f"Submission saved to {self.cache_dir / self.reddit_post['record_file_json']}"
        )

        # Save the submission to a text file
        with open(self.cache_dir / self.reddit_post["record_file_txt"], "w") as text_file:
            text_file.write(unidecode(ftfy.fix_text(submission.title)) + "." + "\n")
            text_file.write(unidecode(ftfy.fix_text(submission.selftext)) + "\n")
        self.logger.info(
            f"Submission text saved to {self.cache_dir / self.reddit_post['record_file_txt']}"
        )

        # return the generated file contents
        with open(self.cache_dir / self.reddit_post["record_file_txt"]) as result_file:
            result_string = result_file.read()
        return result_string

    # @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def fix_text(self, source_txt: str, debug: bool = True) -> str:
        self.logger.info("Setting up language tool text fixer")
        grammar_fixer = language_tool_python.LanguageTool("en-US")

        source_txt = ftfy.fix_text(source_txt)
        source_txt = unidecode(source_txt)
        for escape_char in ESCAPE_CHARACTERS:
            source_txt = source_txt.replace(escape_char, " ")

        sentences = []
        res = []

        for word in source_txt.split(" "):
            if word == "":
                continue
            if word[0] in PUNCTUATIONS:
                sentences.append(" ".join(res))
                res = []
            res.append(word)
            if word[-1] in PUNCTUATIONS:
                sentences.append(" ".join(res))
                res = []

        self.logger.info(
            f"Split text into sentences and fixed text. Found {len(sentences)} sentences"
        )

        corrected_sentences = []
        for sentence in sentences:
            try:
                corrected_sentences.append(grammar_fixer.correct(sentence))
            except Exception as e:
                self.logger.error(f"Error: {e}")
                corrected_sentences.append(sentence)

        grammar_fixer.close()
        result_string = " ".join(corrected_sentences)

        if debug:
            with open(self.cache_dir / "fix_text_debug.txt", "w") as text_file:
                text_file.write(result_string)
            self.logger.info(f"Debug text saved to {self.cache_dir / 'fix_text_debug.txt'}")

        return result_string

    # @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def generate_audio(
        self,
        source_txt: str,
        output_audio: str | None = None,
        output_script_file: str | None = None,
        seed: int | None = None,
    ) -> bool:
        self.audio_cfg = self.cfg["audio"]
        if output_audio is None:
            self.logger.info("No output audio file specified. Generating output audio file")
            if "output_audio_file" in self.audio_cfg:
                output_audio = self.cache_dir / self.audio_cfg["output_audio_file"]
            else:
                output_audio = self.cache_dir / "output.wav"

        if output_script_file is None:
            self.logger.info("No output script file specified. Generating output script file")
            if "output_script_file" in self.audio_cfg:
                output_script_file = self.cache_dir / self.audio_cfg["output_script_file"]
            else:
                output_script_file = self.cache_dir / "generated_audio_script.txt"

        self.logger.info("Generating audio from text")
        for abbreviation, replacement, padding in ABBREVIATION_TUPLES:
            source_txt = abbreviation_replacer(source_txt, abbreviation, replacement, padding)
        source_txt = source_txt.strip()

        for s in source_txt.split(" "):
            if has_alpha_and_digit(s):
                source_txt = source_txt.replace(s, split_alpha_and_digit(s))

        with open(output_script_file, "w") as text_file:
            text_file.write(source_txt)
        self.logger.info(f"Text saved to {output_script_file}")

        if seed is None:
            random.shuffle(VOICES)
            speaker = random.choice(VOICES)
        else:
            speaker = VOICES[seed]

        self.logger.info(f"Generating audio with speaker: {speaker}")

        try:
            tts(source_txt, speaker, output_audio)
            self.logger.info(
                f"Successfully generated audio.\nSpeaker: {speaker}\nOutput path: {output_audio}"
            )
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.logger.error("Failed to generate audio with tiktokvoice")
            return False

        return True

    # function to generate the audio transcript from given audio file and text file.
    # @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def generate_audio_transcript(
        self,
        source_audio_file: Path,
        source_text_file: Path,
        output_transcript_file: str | None = None,
        debug: bool = True,
    ) -> list[dict[str, str | float]]:
        self.audio_cfg = self.cfg["audio"]
        self.logger.info("Generating audio transcript")

        # read the script
        with open(source_text_file) as text_file:
            source_text = text_file.read()

        self.word_transcript = generate_audio_transcription(
            audio_file=str(source_audio_file),
            script=source_text,
            device=self.audio_cfg["device"],
            model=self.audio_cfg["model"],
            batch_size=self.audio_cfg["batch_size"],
            compute_type=self.audio_cfg["compute_type"],
        )

        if output_transcript_file is None:
            output_transcript_file = self.cache_dir / self.audio_cfg["transcript_json"]

        self.logger.info(f"Saving transcript to {output_transcript_file}")

        with open(output_transcript_file, "w") as transcript_file:
            # noinspection PyTypeChecker
            json.dump(
                self.word_transcript,
                transcript_file,
                indent=4,
                skipkeys=True,
                sort_keys=True,
            )

        if debug:
            self.logger.info(pformat(self.transcript))

        return self.word_transcript

    def quit(self) -> None:
        self.logger.debug("Closing and cleaning up resources.")
        # Close the language tool if it was used
        if hasattr(self, "grammar_fixer") and self.grammar_fixer:
            try:
                self.grammar_fixer.close()
            except Exception as e:
                self.logger.error(f"Error closing grammar fixer: {e}")

        # Delete all instance variables
        for attr in list(self.__dict__.keys()):
            try:
                self.logger.debug(f"Deleting {attr}")
                if attr == "logger":
                    continue
                delattr(self, attr)
            except Exception as e:
                self.logger.warning(f"Error deleting {attr}: {e}")

        self.logger.debug("All objects in the class have been deleted.")
        return
