# https://huggingface.co/docs/diffusers/main/en/index
import os
from pathlib import Path
from time import sleep

import torch
import yaml
from diffusers import AutoencoderKL, FluxPipeline
from transformers import CLIPTextModel, T5EncoderModel

from .utils import get_logger

MODEL_UNLOAD_DELAY = 5


class GenerateImage:
    """
    A class for generating images using different Flux models from Hugging Face.

    This class provides methods to load and use various Flux models, including
    FLUX.1-dev, FLUX.1-schnell, and a custom Pixel Wave model. It handles model
    loading, image generation, and resource cleanup.
    """

    def __init__(self, config_file: Path | str) -> None:
        """
        Initializes the GenerateImage class.

        Args:
            config_file (Path | str): Path to the YAML configuration file containing settings
                such as the Hugging Face access token.

        Raises:
            FileNotFoundError: If the specified configuration file does not exist.
            ValueError: If the configuration file is not a YAML file.
        """
        # if config_file is str convert it to a Pathlike
        self.setup_cfg = Path(config_file) if isinstance(config_file, str) else config_file

        if not self.setup_cfg.exists():
            raise FileNotFoundError(f"File {str(self.setup_cfg)} does not exist")

        if self.setup_cfg.suffix != ".yml":
            raise ValueError(f"File {str(self.setup_cfg)} is not a yaml file")

        # load the yml file
        with open(self.setup_cfg) as f:
            self.cfg = yaml.safe_load(f)

        self.logger = get_logger(__name__)

        if "hugging_face_access_token" not in self.cfg:
            self.logger.warning(
                "Please add your huggingface access token to use Flux.1-Dev.\nDefaulting to use Flux.1-Schnell"
            )

        self.pipe: FluxPipeline | None = None

    def _load_model(self, model_id: str) -> bool:
        """
        Loads a Flux model from Hugging Face.

        Args:
            model_id (str): The ID of the Flux model to load from Hugging Face.

        Returns:
            bool: True if the model was loaded successfully.

        Raises:
            RuntimeError: If there is an error loading the Flux model.
        """
        try:
            self.pipe = FluxPipeline.from_pretrained(model_id, torch_dtype=torch.bfloat16)
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
        """
        Generates an image using the FLUX.1-dev model from Hugging Face.

        Args:
            prompt (str): The text prompt to guide image generation.
            output_path (str): The path to save the generated image.
            negative_prompt (str): The text prompt to guide what the model should avoid generating. Defaults to "".
            model_id (str): The ID of the FLUX.1-dev model on Hugging Face. Defaults to "black-forest-labs/FLUX.1-dev".
            steps (int): The number of inference steps. Defaults to 20.
            seed (int): The random seed for image generation. Defaults to 0.
            height (int): The height of the output image. Defaults to 1024.
            width (int): The width of the output image. Defaults to 1024.
            guidance_scale (float): The guidance scale for image generation. Defaults to 3.5.

        Returns:
            bool: True if the image was generated and saved successfully.
        """
        self.logger.info("This image generator uses the Flux Dev model.")
        # Add access token to environment variable
        if "hugging_face_access_token" in self.cfg and os.environ.get("HF_TOKEN") is None:
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
            max_sequence_length=512,
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
        self.logger.info("Wait for 5 seconds, So that the GPU memory can be freed")
        sleep(MODEL_UNLOAD_DELAY)
        return True

    # @retry(max_retries=MAX_RETRIES, delay=DELAY, notify=NOTIFY)
    def use_huggingface_flux_schnell(
        self,
        prompt: str,
        output_path: str,
        negative_prompt: str = "",
        model_id: str = "black-forest-labs/FLUX.1-schnell",
        steps: int = 4,
        seed: int = 0,
        height: int = 1024,
        width: int = 1024,
        guidance_scale: float = 0.0,
    ) -> bool:
        """
        Generates an image using the FLUX.1-schnell model from Hugging Face.

        Args:
            prompt (str): The text prompt to guide image generation.
            output_path (str): The path to save the generated image.
            negative_prompt (str): The text prompt to guide what the model should avoid generating. Defaults to "".
            model_id (str): The ID of the FLUX.1-schnell model on Hugging Face. Defaults to "black-forest-labs/FLUX.1-schnell".
            steps (int): The number of inference steps. Defaults to 4.
            seed (int): The random seed for image generation. Defaults to 0.
            height (int): The height of the output image. Defaults to 1024.
            width (int): The width of the output image. Defaults to 1024.
            guidance_scale (float): The guidance scale for image generation. Defaults to 0.0.

        Returns:
            bool: True if the image was generated and saved successfully.
        """
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
        self.logger.info("Wait for 5 seconds, So that the GPU memory can be freed")
        sleep(MODEL_UNLOAD_DELAY)
        return True

    def use_flux_pixel_wave(
        self,
        prompt: str,
        output_path: str,
        model_id: str = "https://huggingface.co/mikeyandfriends/PixelWave_FLUX.1-schnell_03/blob/main/pixelwave_flux1_schnell_fp8_03.safetensors",
        steps: int = 4,
        seed: int = 595570113709576,
        height: int = 1024,
        width: int = 1024,
        guidance_scale: float = 3.5,
    ) -> bool:
        """
        Generates an image using the custom Flux Pixel Wave model.

        Args:
            prompt (str): The text prompt to guide image generation.
            output_path (str): The path to save the generated image.
            model_id (str): The URL or path to the Pixel Wave model file. Defaults to "https://huggingface.co/mikeyandfriends/PixelWave_FLUX.1-schnell_03/blob/main/pixelwave_flux1_schnell_fp8_03.safetensors".
            steps (int): The number of inference steps. Defaults to 4.
            seed (int): The random seed for image generation. Defaults to 595570113709576.
            height (int): The height of the output image. Defaults to 1024.
            width (int): The width of the output image. Defaults to 1024.
            guidance_scale (float): The guidance scale for image generation. Defaults to 3.5.

        Returns:
            bool: True if the image was generated and saved successfully.
        """
        self.logger.info("This image generator uses the Flux Pixel Wave model.")

        text_encoder = CLIPTextModel.from_pretrained(
            "black-forest-labs/FLUX.1-schnell", subfolder="text_encoder"
        )
        text_encoder_2 = T5EncoderModel.from_pretrained(
            "black-forest-labs/FLUX.1-schnell", subfolder="text_encoder_2"
        )
        vae = AutoencoderKL.from_pretrained("black-forest-labs/FLUX.1-schnell", subfolder="vae")

        self.pipe = FluxPipeline.from_single_file(
            model_id,
            use_safetensors=True,
            torch_dtype=torch.bfloat16,
            # Load additional not included in safetensor
            text_encoder=text_encoder,
            text_encoder_2=text_encoder_2,
            vae=vae,
        )

        # to run on low vram GPUs (i.e. between 4 and 32 GB VRAM)
        # Choose ONE of the following:
        # pipe.enable_model_cpu_offload()  # Best for low-VRAM GPUs
        self.pipe.enable_sequential_cpu_offload()  # Alternative for moderate VRAM GPUs
        self.pipe.vae.enable_slicing()  # Reduces memory usage for decoding
        self.pipe.vae.enable_tiling()  # Further optimizes VAE computation

        # casting here instead of in the pipeline constructor because doing so in the constructor loads all models into CPU memory at once
        self.pipe.to(torch.float16)

        self.logger.info("Generating image")
        image = self.pipe(
            prompt,
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
        del text_encoder
        del text_encoder_2
        del vae

        self.pipe = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.logger.info("Wait for 5 seconds, So that the GPU memory can be freed")
        sleep(MODEL_UNLOAD_DELAY)
        return True

    def quit(self) -> None:
        """
        Cleans up resources and exits the image generator.

        This method clears the CUDA cache (if available) and attempts to
        delete all instance variables to free up memory.
        """
        self.logger.info("Quitting the image generator")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        # Delete all instance variables
        for attr in list(self.__dict__.keys()):
            try:
                self.logger.debug(f"Deleting {attr}")
                if attr == "logger":
                    continue
                delattr(self, attr)
            except Exception as e:
                self.logger.error(f"Error deleting {attr}: {e}")
        return None
