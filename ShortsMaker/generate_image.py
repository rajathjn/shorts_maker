# https://huggingface.co/docs/diffusers/main/en/index
import logging
import os
from pathlib import Path
from typing import DefaultDict, Optional

import torch
import yaml
from diffusers import FluxPipeline

from .logging_config import setup_package_logging


class GenerateImage:
    def __init__(self, config_file: Path, logging_config: DefaultDict = None) -> None:

        # if config_file is str convert it to a Pathlike
        self.setup_cfg = (
            Path(config_file) if isinstance(config_file, str) else config_file
        )

        if not self.setup_cfg.exists():
            raise FileNotFoundError(f"File {str(self.setup_cfg)} does not exist")

        if self.setup_cfg.suffix != ".yml":
            raise ValueError(f"File {str(self.setup_cfg)} is not a yaml file")

        # load the yml file
        with open(self.setup_cfg, "r") as f:
            self.cfg = yaml.safe_load(f)

        # check if logging is set up in config_file
        self.logging_cfg = {
            "log_file": "generate_image.log",
            "logger_name": "GenerateImage",
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

        if "hugging_face_access_token" not in self.cfg:
            self.logger.warning(
                "Please add your huggingface access token to use Flux.1-Dev.\n"
                "Defaulting to use Flux.1-Schnell"
            )

        self.pipe: Optional[FluxPipeline] = None

    def _load_model(self, model_id: str) -> bool:

        try:
            self.pipe = FluxPipeline.from_pretrained(
                model_id, torch_dtype=torch.bfloat16
            )
            self.logger.info(f"Loading Flux model from {model_id}")
            # to run on low vram GPUs (i.e. between 4 and 32 GB VRAM)
            # Choose ONE of the following:
            # pipe.enable_model_cpu_offload()  # Best for low-VRAM GPUs
            self.pipe.enable_sequential_cpu_offload()  # Alternative for moderate VRAM GPUs
            self.pipe.vae.enable_slicing()  # Reduces memory usage for decoding
            self.pipe.vae.enable_tiling()  # Further optimizes VAE computation

            # casting here instead of in the pipeline constructor because doing so in the constructor loads all models into CPU memory at once
            self.pipe.to(torch.float16)

            self.logger.info("Flux model loaded")
            return True
        except Exception as e:
            self.logger.error(e)
            raise RuntimeError("Error in loading the Flux model")

    # @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def use_huggingface_flux_dev(
        self,
        prompt: str,
        output_path: str,
        negative_prompt: str = "",
        model_id: str = "black-forest-labs/FLUX.1-dev",
        steps: int = 20,
        seed: int = 0,
        height: int = 1024,
        width: int = 1024,
        guidance_scale: float = 3.5,
    ) -> bool:

        self.logger.info("This image generator uses the Flux Dev model.")
        # Add access token to environment variable
        if (
            "hugging_face_access_token" in self.cfg
            and os.environ.get("HF_TOKEN") is None
        ):
            self.logger.info("Setting HF_TOKEN environment variable")
            os.environ["HF_TOKEN"] = self.cfg["hugging_face_access_token"]

        self._load_model(model_id)

        self.logger.info("Generating image")
        image = self.pipe(
            prompt,
            negative_prompt,
            guidance_scale=guidance_scale,
            output_type="pil",
            num_inference_steps=steps,
            height=height,
            width=width,
            generator=torch.Generator("cpu").manual_seed(seed),
        ).images[0]
        image.save(output_path)
        self.logger.info(f"Image saved to {output_path}")

        del self.pipe
        self.pipe = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return True

    # @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def use_huggingface_flux_schnell(
        self,
        prompt: str,
        output_path: str,
        negative_prompt: str = "",
        model_id: str = "black-forest-labs/FLUX.1-schnell",
        steps: int = 20,
        seed: int = 0,
        height: int = 1024,
        width: int = 1024,
        guidance_scale: float = 0.0,
    ) -> bool:

        self.logger.info("This image generator uses the Flux Schnell model.")

        self._load_model(model_id)

        self.logger.info("Generating image")
        image = self.pipe(
            prompt,
            negative_prompt,
            guidance_scale=guidance_scale,
            output_type="pil",
            num_inference_steps=steps,
            max_sequence_length=256,
            height=height,
            width=width,
            generator=torch.Generator("cpu").manual_seed(seed),
        ).images[0]
        image.save(output_path)
        self.logger.info(f"Image saved to {output_path}")

        del self.pipe
        self.pipe = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return True
