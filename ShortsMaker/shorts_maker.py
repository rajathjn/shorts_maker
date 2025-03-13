import json
import secrets
from collections.abc import Generator
from pathlib import Path
from pprint import pformat
from typing import Any

import ftfy
import language_tool_python
import praw
import yaml
from praw.models import Submission, Subreddit
from unidecode import unidecode

from .utils import VOICES, generate_audio_transcription, get_logger, retry, tts

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


def abbreviation_replacer(text: str, abbreviation: str, replacement: str, padding: str = "") -> str:
    """
    Replaces all occurrences of an abbreviation within a given text with a specified replacement.

    This function allows replacing abbreviations with a replacement string while considering optional padding
    around the abbreviation. Padding ensures the abbreviation is correctly replaced regardless of its position
    in the text or the surrounding characters.

    Args:
        text (str): The text where the abbreviation occurrences should be replaced.
        abbreviation (str): The abbreviation to be replaced in the text.
        replacement (str): The string to replace the abbreviation with.
        padding (str, optional): Additional characters surrounding the abbreviation, making the
            replacement match more specific. Default is an empty string.

    Returns:
        str: The text with all occurrences of the abbreviation replaced by the replacement string.
    """
    text = text.replace(abbreviation + padding, replacement)
    text = text.replace(padding + abbreviation, replacement)
    return text


def has_alpha_and_digit(word: str) -> bool:
    """
    Determines if a string contains both alphabetic and numeric characters.

    This function checks whether the given string contains at least one alphabetic
    character and at least one numeric character. It utilizes Python's string methods
    to identify the required character types.

    Args:
        word: The string to check for the presence of alphabetic and numeric
            characters.

    Returns:
        bool: True if the string contains at least one alphabetic character and one
            numeric character, otherwise False.
    """
    return any(character.isalpha() for character in word) and any(
        character.isdigit() for character in word
    )


def split_alpha_and_digit(word):
    """
    Splits a given string into separate segments of alphabetic and numeric sequences.

    This function processes each character in the input string and divides it into
    distinct groups of alphabetic sequences and numeric sequences. A space is added
    between these groups whenever a transition occurs between alphabetic and numeric
    characters, or vice versa. Non-alphanumeric characters are included as is without
    causing a split.

    Args:
        word (str): The input string to be split into alphabetic and numeric
            segments.

    Returns:
        str: A string where alphabetic and numeric segments from the input are
            separated by a space while retaining other characters.
    """
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
    """
    Represents a utility class to facilitate the creation of video shorts from
    text and audio assets. The class manages configuration, logging, processing
    of text for audio generation, reddit post retrieval, and asset handling among
    other operations.

    The `ShortsMaker` class is designed to be highly extensible and configurable
    via YAML configuration files. It includes robust error handling for invalid
    or missing configuration files and directories. The functionality also integrates
    with external tools such as Reddit API and grammar correction tools to streamline
    the process of creating video shorts.

    Attributes:
        VALID_CONFIG_EXTENSION (str): Expected file extension for configuration files.
        setup_cfg (Path): Path of the validated configuration file.
        cfg (dict): Parsed configuration from the loaded configuration file.
        cache_dir (Path): Directory for storing temporary files and intermediate data.
        logging_cfg (dict): Configuration for setting up logging.
        logger (Logger): Logger instance used for logging events and errors.
        retry_cfg (dict): Configuration parameters for retry logic, including maximum
            retries and delay between retries.
        word_transcript (str | None): Transcript represented as individual words.
        line_transcript (str | None): Transcript represented as individual lines.
        transcript (str | None): Full transcript derived from the Reddit post or input text.
        audio_cfg (dict | None): Configuration details specific to audio processing.
        reddit_post (dict | None): Details related to the Reddit post being processed.
        reddit_cfg (dict | None): Configuration details specific to Reddit API integration.
    """

    VALID_CONFIG_EXTENSION = ".yml"

    def __init__(self, config_file: Path | str) -> None:
        self.setup_cfg = self._validate_config_path(config_file)
        self.cfg = self._load_config()
        self.logger = get_logger(__name__)
        self.cache_dir = self._setup_cache_directory()
        self.retry_cfg = self._setup_retry_config()

        # Initialize other instance variables
        self.word_transcript: str | None = None
        self.line_transcript: str | None = None
        self.transcript: str | None = None
        self.audio_cfg: dict | None = None
        self.reddit_post: dict | None = None
        self.reddit_cfg: dict | None = None

    def _validate_config_path(self, config_file: Path | str) -> Path:
        """
        Validates the given configuration file path to ensure it exists and has the correct format.

        This method checks whether the provided file path points to an actual file and
        whether its extension matches the expected configuration file format. If any
        of these conditions are not met, appropriate exceptions are raised.

        Args:
            config_file: A file path string or a Path object representing the
                configuration file to be validated.

        Returns:
            The validated configuration file path as a Path object.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            ValueError: If the configuration file format is invalid.
        """
        config_path = Path(config_file) if isinstance(config_file, str) else config_file
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        if config_path.suffix != self.VALID_CONFIG_EXTENSION:
            raise ValueError(
                f"Invalid configuration file format. Expected {self.VALID_CONFIG_EXTENSION}"
            )
        return config_path

    def _load_config(self) -> dict[str, Any]:
        """
        Loads and parses configuration data from a YAML file.

        This method attempts to open and parse a YAML configuration file specified
        by the `setup_cfg` attribute of the class. If the file does not contain valid
        YAML or cannot be read, it raises an exception with an appropriate error message.

        Returns:
            Dict[str, Any]: A dictionary representation of the loaded YAML configuration.

        Raises:
            ValueError: If the YAML file contains invalid content or cannot be parsed.
        """
        try:
            with open(self.setup_cfg) as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")

    def _setup_cache_directory(self) -> Path:
        """
        Sets up the cache directory based on the configuration and ensures its existence.

        This method retrieves the cache directory path from the configuration, creates the
        directory (including any required parent directories), and returns the Path object
        representing the cache directory. If the directory already exists, it will not attempt
        to create it again.

        Returns:
            Path: A Path object representing the cache directory.
        """
        if "cache_dir" not in self.cfg:
            self.logger.info("Cache directory not specified, creating it.")
            self.cfg["cache_dir"] = Path.cwd()
        cache_dir = Path(self.cfg["cache_dir"])
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _setup_retry_config(self) -> dict[str, Any]:
        """
        Configures the retry mechanism based on the settings provided in the
        configuration. If retry is disabled, it updates the retry settings to default
        values. Updates global constants to reflect the current retry configuration.

        Returns:
            Dict[str, Any]: The updated retry configuration dictionary.
        """
        retry_config = dict()
        if "retry" not in self.cfg:
            retry_config = {"max_retries": 1, "delay": 0, "notify": False}
        if "retry" in self.cfg:
            retry_config.update(self.cfg["retry"])

        global MAX_RETRIES, DELAY, NOTIFY
        MAX_RETRIES = retry_config["max_retries"]
        DELAY = retry_config["delay"]
        NOTIFY = retry_config["notify"]

        return retry_config

    def get_submission_from_subreddit(
        self, reddit: praw.Reddit, subreddit_name: str
    ) -> Generator[Submission]:
        """
        Retrieves a unique Reddit submission from a specified subreddit.

        Args:
            reddit (praw.Reddit): An instance of the Reddit API client.
            subreddit_name (str): The name of the subreddit to fetch submissions from.
            submission_category (str): The category of submissions to filter by (e.g., "hot", "new") TODO.

        Returns:
            Submission: A unique Reddit submission object.
        """
        subreddit: Subreddit = reddit.subreddit(subreddit_name)
        self.logger.info(f"Subreddit title: {subreddit.title}")
        self.logger.info(f"Subreddit display name: {subreddit.display_name}")
        yield from subreddit.hot()

    def is_unique_submission(self, submission: Submission) -> bool:
        """
        Checks if the given Reddit submission is unique based on its ID.

        Args:
            submission (Submission): The Reddit submission to check.

        Returns:
            bool: True if the submission is unique, False otherwise.
        """
        submission_dirs = self.cache_dir / "reddit_submissions"
        submission_dirs.mkdir(parents=True, exist_ok=True)
        self.logger.debug("Checking if submission is unique")
        self.logger.debug(f"Submission ID: {submission.id}")
        if any(f"{submission.name}.json" == file.name for file in submission_dirs.iterdir()):
            self.logger.info(f"Submission {submission.name} - '{submission.title}' already exists")
            return False
        else:
            with open(submission_dirs / f"{submission.name}.json", "w") as record_file:
                # Object of type Reddit is not JSON serializable, hence need to use vars
                json.dump(
                    {key: str(value) for key, value in vars(submission).items()},
                    record_file,
                    indent=4,
                    skipkeys=True,
                    sort_keys=True,
                )
            self.logger.debug("Unique submission found")
            self.logger.info(f"Submission saved to {submission_dirs / f'{submission.name}.json'}")
        return True

    @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def get_reddit_post(self, url: str | None = None) -> str:
        """
        Retrieves a random top Reddit post from a specified subreddit, saves the post details
        to both a JSON file and a text file, and returns the text content of the post.

        Args:
            url (str | None): The URL of the Reddit post to retrieve. If None, a random top post is retrieved.

        Returns:
            str: The text content of the retrieved Reddit post.

        Raises:
            ValueError: If any value processing errors occur.
            IOError: If file handling (reading/writing) fails.
            praw.exceptions.PRAWException: If PRAW encounters an API or authentication issue.
        """
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

        if url:
            submission = reddit.submission(url=url)
        else:
            for submission_found in self.get_submission_from_subreddit(
                reddit, self.reddit_post["subreddit_name"]
            ):
                if self.is_unique_submission(submission_found):
                    submission = submission_found
                    break

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

    @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def fix_text(self, source_txt: str, debug: bool = True) -> str:
        """
        Fixes and corrects grammatical and textual issues in the provided text input using language processing tools.
        The method processes the input text by fixing encoding issues, normalizing it, splitting it into sentences,
        and then correcting the grammar of each individual sentence. An optional debug mode saves the processed text
        to a debug file for inspection.

        Args:
            source_txt: The text to be processed and corrected.
            debug: If True, saves the corrected text to a debug file for further analysis.

        Returns:
            str: The corrected and formatted text.

        Raises:
            Exception: Raised if errors occur during text correction within individual sentences.
        """
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

    @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def generate_audio(
        self,
        source_txt: str,
        output_audio: str | None = None,
        output_script_file: str | None = None,
        seed: str | None = None,
    ) -> bool:
        """
        Generates audio from a given textual input. The function processes the input text,
        performs text transformations (e.g., replacing abbreviations and splitting alphanumeric
        combinations), and uses a synthesized voice to create an audio file. It also writes the
        processed script to a text file. Speaker selection is either randomized or based on the
        provided seed.

        Args:
            source_txt (str): The input text to be converted into audio.
            output_audio (str | None): The path to save the generated audio. If not provided, a
                default path is generated based on the configuration or cache directory.
            output_script_file (str | None): The file path to save the processed text script. If
                not provided, a default path is generated based on the configuration or cache
                directory.
            seed (str | None): An optional seed to determine the choice of speaker. If not
                provided, the function randomly selects a speaker. Refer to VOICES for available
                speakers.

        Returns:
            bool: Returns True if the audio generation is successful; False otherwise.

        Raises:
            Exception: If an error occurs during text-to-speech processing.
        """
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
            speaker = secrets.choice(VOICES)
        else:
            speaker = seed

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

    @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def generate_audio_transcript(
        self,
        source_audio_file: Path | str,
        source_text_file: Path | str,
        output_transcript_file: str | None = None,
        debug: bool = True,
    ) -> list[dict[str, str | float]]:
        """
        Generates an audio transcript by processing a source audio file and its corresponding text
        file, using predefined configurations such as model, device, and batch size. Saves the
        resulting transcript into a specified output file or a default cache location. Additionally,
        provides an option to enable debug logging.

        Args:
            source_audio_file (Path): The source audio file to be transcribed.
            source_text_file (Path): The text file containing the corresponding script.
            output_transcript_file (str | None): The file where the resulting transcript will be saved.
                Defaults to a predefined location if not specified.
            debug (bool): Whether to enable debug logging of the processed transcript.

        Returns:
            list[dict[str, str | float]]: A list of word-level transcription data, where each entry
            contains word-related information such as timestamps and confidence scores.
        """
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
        self.word_transcript = self._filter_word_transcript(self.word_transcript)

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
            self.logger.info(pformat(self.word_transcript))

        return self.word_transcript

    def _filter_word_transcript(
        self, transcript: list[dict[str, str | float]]
    ) -> list[dict[str, str | float]]:
        # filter entries which have a start time of 0 and end time of greater than 5s
        return [
            entry
            for entry in transcript
            if entry["start"] > 0 and (entry["end"] - entry["start"]) < 5
        ]

    def quit(self) -> None:
        """
        Closes and cleans up resources used in the class instance.

        This method ensures that all resources, tools, and variables used within the
        class instance are properly closed or removed to prevent memory leaks or issues
        when the instance is no longer in use. It includes closing language tools, if
        utilized, and deleting all instance variables except the logger.

        Raises:
            Exception: If there is an issue closing the grammar fixer or deleting
                instance variables. Specific details are logged.

        Returns:
            None: This method does not return any value.
        """
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
