import logging
import platform
import subprocess
import time
from collections import defaultdict
from pathlib import Path

import ollama
import psutil
import yaml
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from .utils import setup_package_logging


class OllamaServiceManager:
    def __init__(
        self,
        logger: logging.Logger | None = None,
    ):
        self.system = platform.system().lower()
        self.process = None
        self.ollama = ollama

        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.name = "OllamaServiceManager"
        self.logger.info(f"Ollama service ollama_service_manager initialized on {self.system}")

    def start_service(self) -> bool:
        # Start the Ollama service based on the operating system
        self.logger.info("Starting Ollama service")
        try:
            if self.system == "windows":
                ollama_execution_command = ["ollama app.exe", "serve"]
            else:
                ollama_execution_command = ["ollama", "serve"]
            self.process = subprocess.Popen(
                ollama_execution_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Wait a moment for the service to start
            time.sleep(2)

            # Check if the service started successfully
            if self.process.poll() is None:
                self.logger.info("Ollama service started successfully")
                return True
        except Exception as e:
            self.logger.error(f"Error starting Ollama service: {str(e)}")
            raise e
            return False

    def stop_service(self) -> bool:
        # Stop the Ollama service
        try:
            if self.process:
                if self.system == "windows":
                    # For Windows
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "ollama app.exe"], capture_output=True, text=True
                    )
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True, text=True
                    )
                else:
                    # For Linux/MacOS
                    self.process.terminate()
                    self.process.wait(timeout=5)
                del self.process
                self.process = None
                self.logger.info("Ollama service stopped successfully")
                return True
            else:
                self.logger.warning("Ollama service either started by user or has already stopped")
                return False

        except Exception as e:
            print(f"Error stopping Ollama service: {str(e)}")
            return False

    @staticmethod
    def is_ollama_running():
        """Check if Ollama is already running."""
        for proc in psutil.process_iter(["name", "cmdline"]):
            try:
                if "ollama" in proc.info["name"].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def is_service_running(self) -> bool:
        # Check if the Ollama service is running
        if self.process and self.process.poll() is None:
            return True
        if self.is_ollama_running():
            return True
        return False

    def get_running_models(self):
        return self.ollama.ps()

    def stop_running_model(self, model_name: str):
        try:
            stop_attempt = subprocess.check_output(
                ["ollama", "stop", model_name], stderr=subprocess.STDOUT, text=True
            )
            self.logger.info(
                f"Ollama service with {model_name} stopped successfully: {stop_attempt}"
            )
            return True
        except Exception as e:
            self.logger.warning(f"Failed to stop {model_name}")
            self.logger.warning(
                "Either the model was already stopped, or the Ollama service is already stopped"
            )
            self.logger.error(f"Error stopping Ollama service: {str(e)}")
            return False

    def get_llm_model(self, model_name: str):
        return self.ollama.pull(model_name)

    def get_list_of_downloaded_files(self) -> list[str]:
        model_list = []
        try:
            model_list = list(self.ollama.list())  # list[tuple[model, list[models]]]
            model_list = [i.model for i in model_list[0][1]]
        except Exception as e:
            self.logger.error(f"Error getting list of downloaded files: {str(e)}")
        return model_list


class AskLLM:
    def __init__(
        self,
        config_file: Path | str,
        model_name: str = "llama3.1:latest",
        temperature: float = 0,
        logging_config: defaultdict = None,
    ) -> None:
        # if config_file is str convert it to a Pathlike
        self.setup_cfg = Path(config_file) if isinstance(config_file, str) else config_file

        if not self.setup_cfg.exists():
            raise FileNotFoundError(f"File {str(self.setup_cfg)} does not exist")

        if self.setup_cfg.suffix != ".yml":
            raise ValueError(f"File {str(self.setup_cfg)} is not a yaml file")

        # load the yml file
        with open(self.setup_cfg) as f:
            self.cfg = yaml.safe_load(f)

        # check if logging is set up in config_file
        self.logging_cfg = {
            "log_file": "AskLLM.log",
            "logger_name": "AskLLM",
            "level": logging.INFO,
            "enable": True,
        }

        if "logging" in self.cfg:
            # override with values in from the setup.yml file
            for key, value in self.cfg["logging"].items():
                self.logging_cfg[key] = value

        if logging_config is not None:
            # override with values defined in logging_config
            for key, value in logging_config.items():
                self.logging_cfg[key] = value

        self.logger = setup_package_logging(**self.logging_cfg)

        self.self_started_ollama: bool = False
        self.ollama_service_manager = OllamaServiceManager(logger=self.logger)
        self.model_name = model_name
        self.model_temperature = temperature
        self.llm: ChatOllama = self._load_llm_model(self.model_name, self.model_temperature)
        self.structured_llm = None

    def _load_llm_model(self, model_name: str, temperature: float) -> ChatOllama:
        if not self.ollama_service_manager.is_service_running():
            self.logger.warning("Ollama service is not running. Attempting to start it.")
            self.ollama_service_manager.start_service()
            self.self_started_ollama = True
            self.logger.warning(f"Self started ollama service: {self.self_started_ollama}")
        self.logger.info("Ollama service found")

        if model_name not in self.ollama_service_manager.get_list_of_downloaded_files():
            self.logger.info(f"Downloading model {model_name}")
            self.ollama_service_manager.get_llm_model(model_name)
            self.logger.info(f"Model {model_name} downloaded")
        else:
            self.logger.info(f"Model {model_name} already downloaded")

        return ChatOllama(model=model_name, temperature=temperature)

    def invoke(self, input_text: str) -> dict | BaseModel:
        prompt = ChatPromptTemplate(
            messages=[
                SystemMessage(
                    "You are a Youtubers digital assistant. Please provide creative, engaging, clickbait, key word rich and accurate information to the user."
                ),
                SystemMessage(
                    "The Youtuber which runs an AI automated Youtube channel. The entire process involves me finding a script, making a video about it, and then using an AI image creator to make a thumbnail for the video."
                ),
                SystemMessage(
                    "Be short and concise. Be articulate, no need to be verbose and justify your answer."
                ),
                HumanMessage(f"Script:\n{input_text}"),
            ],
        )
        self.structured_llm = self.llm.with_structured_output(YoutubeDetails, include_raw=True)
        return self.structured_llm.invoke(prompt.messages)

    def invoke_image_describer(self, script: str, input_text: str) -> dict | BaseModel:
        prompt = ChatPromptTemplate(
            messages=[
                SystemMessage(
                    "You are an AI image prompt generator, who specializes in image description. Helping users to create AI image prompts."
                ),
                SystemMessage(
                    "The user provides the complete and the text to generate the prompt for. You should provide a detailed and creative description of an image. Note: Avoid mentioning names or text titles to be in the description. The more detailed and imaginative your description, the more interesting the resulting image will be."
                ),
                SystemMessage("Keep the description with 500 characters or less."),
                HumanMessage(f"Script:\n{script}"),
                HumanMessage(f"Text:\n{input_text}"),
            ]
        )
        self.structured_llm = self.llm.with_structured_output(ImageDescriber, include_raw=True)
        return self.structured_llm.invoke(prompt.messages)

    def quit_llm(self):
        self.ollama_service_manager.stop_running_model(self.model_name)
        if self.self_started_ollama:
            self.ollama_service_manager.stop_service()
        # Delete all instance variables
        for attr in list(self.__dict__.keys()):
            try:
                self.logger.debug(f"Deleting {attr}")
                if attr == "logger":
                    continue
                delattr(self, attr)
            except Exception as e:
                self.logger.error(f"Error deleting {attr}: {e}")
        return


# Pydantic YoutubeDetails
class YoutubeDetails(BaseModel):
    """Details of the YouTube video."""

    title: str = Field(
        description="A fun and engaging title for the Youtube video. Has to be related to the reddit post and is not more than 100 characters."
    )
    description: str = Field(
        description="Description of the Youtube video. It should be a simple summary of the video."
    )
    tags: list[str] = Field(
        description="Tags of the Youtube video. tags are single words with no space in them."
    )
    thumbnail_description: str = Field(
        description="Thumbnail description of the Youtube video. provide detailed and creative descriptions that will inspire unique and interesting images from the AI. Keep in mind that the AI is capable of understanding a wide range of language and can interpret abstract concepts, so feel free to be as imaginative and descriptive as possible. For example, you could describe a scene from a futuristic city, or a surreal landscape filled with strange creatures. The more detailed and imaginative your description, the more interesting the resulting image will be."
    )


# Image Describer
class ImageDescriber(BaseModel):
    """Given text, Provides a detailed and creative description for an image."""

    description: str = Field(
        description="Provide a detailed and creative description that will inspire unique and interesting images from the AI. Keep in mind that the AI is capable of understanding a wide range of language and can interpret abstract concepts, so feel free to be as imaginative and descriptive as possible. For example, you could describe the scene in a pictorial way adding more details or elaborating the scenario. The more detailed and imaginative your description, the more interesting the resulting image will be."
    )
