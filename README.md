# ShortsMaker

[![ShortsMaker](https://github.com/rajathjn/youtube_shorts_automation/actions/workflows/python-app.yml/badge.svg)](https://github.com/rajathjn/youtube_shorts_automation/actions/workflows/python-app.yml)

ShortsMaker is a Python package designed to facilitate the creation of engaging short videos or social media clips. It leverages a variety of external services and libraries to streamline the process of generating, processing, and uploading short content.

## Support Me
Like what I do, Please consider supporting me.

<a href="https://coindrop.to/martisjnx" target="_blank"><img src="https://coindrop.to/embed-button.png" style="border-radius: 10px;" alt="Coindrop.to me" style="height: 57px !important;width: 229px !important;" ></a>

## Table of Contents

- [ShortsMaker](#shortsmaker)
  - [Support Me](#support-me)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [External Dependencies](#external-dependencies)
  - [Environment Variables](#environment-variables)
  - [Usage](#usage)
  - [Example Video](#example-video)
  - [TODO](#todo)
  - [Development](#development)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- **Automated Content Creation:** Easily generate engaging short videos.
- **External Service Integration:** Seamlessly integrates with services like Discord for notifications.
- **GPU-Accelerated Processing:** Optional GPU support for faster processing using whisperx.
- **Modular Design:** Built with extensibility in mind.
- **In Development:** AskLLM AI agent now fully integrated for generating metadata and creative insights.
- **In Development:** GenerateImage class enhanced for text-to-image generation using flux. May be resource intensive.

## Requirements

- **Python:** 3.12.8
- **Package Manager:** `uv` is used for package management.
- **Operating System:** Windows, Mac, or Linux (ensure external dependencies are installed for your platform)

## Installation

1. **Clone the Repository:**

   ```bash
   git clone <repository-url>
   cd ShortsMaker
   ```

2. **Install the Package Using uv:**

   ```bash
   uv pip install -r pyproject.toml

   or

   uv sync
   uv sync --extra cpu # for cpu
   uv sync --extra cu124 # for cuda 12.4 versions
   ```

3. **Install Any Additional Python Dependencies:**

   If not automatically managed by uv, you may install them using pip:

   ```bash
   pip install -r requirements.txt
   ```

## External Dependencies

ShortsMaker relies on several external non-Python components. Please ensure the following are installed/configured on your system:

- **Discord Notifications:**
  - You must set the Discord webhook token (`DISCORD_WEBHOOK_URL`) as an environment variable.

- **Ollama:**
  - The external tool Ollama must be installed on your system. Refer to the [Ollama documentation](https://ollama.com/) for installation details.

- **WhisperX (GPU Acceleration):**
  - For GPU execution, ensure that the NVIDIA libraries are installed on your system:
    - **cuBLAS:** Version 11.x
    - **cuDNN:** Version 8.x
  - These libraries are required for optimal performance when using whisperx for processing.

## Environment Variables

Before running ShortsMaker, make sure you set the necessary environment variables:

- **DISCORD_WEBHOOK_TOKEN:**
  This token is required for sending notifications through Discord.
  Example (Windows Command Prompt):

  ```batch
  set DISCORD_WEBHOOK_TOKEN=your_discord_webhook_token_here
  ```

  Example (Linux/macOS):

  ```bash
  export DISCORD_WEBHOOK_TOKEN=your_discord_webhook_token_here
  ```

## Usage

Ensure you have a `setup.yml` configuration file in the `youtube_shorts_automation` directory. Use the [example-setup.yml](example.setup.yml) as a reference.

Below is a basic example to get you started with ShortsMaker:

```python
from ShortsMaker import MoviepyCreateVideo, ShortsMaker, AskLLM, GenerateImage
import yaml
from pathlib import Path

setup_file = "youtube_shorts_automation/setup.yml"
with open(setup_file) as f:
    cfg = yaml.safe_load(f)

get_post = ShortsMaker(setup_file)
get_post.get_reddit_post()
with open(Path(cfg["cache_dir"])/cfg["reddit_post_getter"]["record_file_txt"]) as f:
    script = f.read()

get_post.generate_audio(script)
get_post.generate_audio_transcript(
    source_audio_file = f"{cfg['cache_dir']}/{cfg['audio']['output_audio_file']}",
    source_text_file = f"{cfg['cache_dir']}/{cfg['audio']['output_script_file']}"
)
get_post.quit()

create_video = MoviepyCreateVideo(config_file=setup_file)
create_video()
create_video.quit()

ask_llm = AskLLM(config_file=setup_file)
result = ask_llm.invoke(script)
print(result["parsed"].title)
print(result["parsed"].description)
print(result["parsed"].tags)
print(result["parsed"].thumbnail_description)
ask_llm.quit_llm()

# You can use, AskLLM to generate a text prompt for the image generation as well
# image_description = ask_llm.invoke_image_describer(script = script, input_text = "A wild scenario")
# print(image_description)
# print(image_description["parsed"].description)

# Generate image uses a lot of resources so beware
# generate_image = GenerateImage(config_file=setup_file)
# generate_image.use_huggingface_flux_schnell(image_description["parsed"].description, "output.png")
# generate_image.quit()
```

## Example Video

https://github.com/user-attachments/assets/6aad212a-bfd5-4161-a2bc-67d24a8de37f

## TODO
- [ ] Dockerize the project, To avoid the complex set up process.
- [x] Add an example video to the README.

## Development

If you want to contribute to the project, please follow these steps:

1. **Set up the development environment:**
   - Ensure you have Python 3.12.8 and uv installed.
   - Clone the repository and install the development dependencies.

2. **Run the Tests:**
   - Tests are located in the `tests/` directory.
   - Run tests using:

     ```bash
     uv run --frozen pytest
     ```

## Contributing

If you want to contribute to the project, please follow these steps:

Follow everything in the [Development](#development) section and then:

**Submit a Pull Request:**
   - Fork the repository.
   - Create a new branch for your feature or bugfix.
   - Commit your changes and push the branch to your fork.
   - Open a pull request with a detailed description of your changes.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
