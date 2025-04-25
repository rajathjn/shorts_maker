# ShortsMaker

[![ShortsMaker](https://github.com/rajathjn/shorts_maker/actions/workflows/python-app.yml/badge.svg)](https://github.com/rajathjn/shorts_maker/actions/workflows/python-app.yml)
[![CodeQL](https://github.com/rajathjn/shorts_maker/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/rajathjn/shorts_maker/actions/workflows/github-code-scanning/codeql)

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
  - [Usage Via Docker](#usage-via-docker)
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
- **Package Manager:** [`uv`](https://docs.astral.sh/uv/) is used for package management. ( It's amazing! try it out. )
- **Operating System:** Windows, Mac, or Linux (ensure external dependencies are installed for your platform)

## Usage Via Docker

To use ShortsMaker via Docker, follow these steps:

1. **Build the Docker Image:**

   Build the Docker image using the provided Dockerfile.

   ```bash
   docker build -t shorts_maker -f Dockerfile .
   ```

2. **Run the Docker Container:**

   For the first time, run the container with the necessary mounts, container name, and working directory set.

   ```bash
   docker run --name shorts_maker_container -v $pwd/assets:/shorts_maker/assets -w /shorts_maker -it shorts_maker bash
   ```

3. **Start the Docker Container:**

   If the container was previously stopped, you can start it again using:

   ```bash
   docker start shorts_maker_container
   ```

4. **Access the Docker Container:**

   Execute a bash shell inside the running container.

   ```bash
   docker exec -it shorts_maker_container bash
   ```

5. **Run Examples and Tests:**

   Once you are in the bash shell of the container, you can run the example script or tests using `uv`.

   To run the example script:

   ```bash
   uv run example.py
   ```

   To run tests:

   ```bash
   uv run pytest
   ```

**Note:** If you plan to use `ask_llm` or `generate_image`, it is not recommended to use the Docker image due to the high resource requirements of these features. Instead, run ShortsMaker directly on your host machine.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/rajathjn/shorts_maker
   cd shorts_maker
   ```

2. **Install the Package Using uv:**

   Note: Before starting the installation process. Ensure a python3.12 virtual environment is set up.

   ```bash
   uv venv -p 3.12 .venv

   or

   python -m venv .venv
   ```

   Package Installation.

   ```bash
   uv pip install -r pyproject.toml

   or

   uv sync
   uv sync --extra cpu # for cpu
   uv sync --extra cu124 # for cuda 12.4 versions
   ```

4. **Install Any Additional Python Dependencies:**

   If not automatically managed by uv, you may install them using pip ( In most cases you do not need to use the below. ):

   ```bash
   pip install -r requirements.txt
   ```

## External Dependencies

ShortsMaker relies on several external non-Python components. Please ensure the following are installed/configured on your system:

- **Discord Notifications:**
  - You must set your Discord webhook URL (`DISCORD_WEBHOOK_URL`) as an environment variable.
  - Refer to the [Discord documentation](https://discord.com/developers/docs/resources/webhook#create-webhook) for creating a webhook.
  - If you don't want to use Discord notifications, you can set `DISCORD_WEBHOOK_URL` to `None` or do something like

  ```python
  import os
  os.environ["DISCORD_WEBHOOK_URL"] = "None"
  ```

- **Ollama:**
  - The external tool Ollama must be installed on your system. Refer to the [Ollama documentation](https://ollama.com/) for installation details.

- **WhisperX (GPU Acceleration):**
  - For GPU execution, ensure that the NVIDIA libraries are installed on your system:
    - **cuBLAS:** Version 11.x
    - **cuDNN:** Version 8.x
  - These libraries are required for optimal performance when using whisperx for processing.

## Environment Variables

Before running ShortsMaker, make sure you set the necessary environment variables:

- **DISCORD_WEBHOOK_URL:**
  This token is required for sending notifications through Discord.
  Example (Windows Command Prompt):

  ```powershell
  set DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
  ```

  Example (Linux/macOS):

  ```bash
  export DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
  ```

  From Python:

  ```python
  import os
  os.environ["DISCORD_WEBHOOK_URL"] = "your_discord_webhook_url_here"
  ```

## Usage

Ensure you have a `setup.yml` configuration file in the `shorts_maker` directory. Use the [example-setup.yml](example.setup.yml) as a reference.

Below is a basic example to get you started with ShortsMaker:

You can also refer to the same [here](example.py)

```python
from pathlib import Path

import yaml

from ShortsMaker import MoviepyCreateVideo, ShortsMaker

setup_file = "setup.yml"

with open(setup_file) as f:
    cfg = yaml.safe_load(f)

get_post = ShortsMaker(setup_file)

# You can either provide an URL for the reddit post
get_post.get_reddit_post(
    url="https://www.reddit.com/r/Python/comments/1j36d7a/i_got_tired_of_ai_shorts_scams_so_i_built_my_own/"
)
# Or just run the method to get a random post from the subreddit defined in setup.yml
# get_post.get_reddit_post()

with open(Path(cfg["cache_dir"]) / cfg["reddit_post_getter"]["record_file_txt"]) as f:
    script = f.read()

get_post.generate_audio(
    source_txt=script,
    output_audio=f"{cfg['cache_dir']}/{cfg['audio']['output_audio_file']}",
    output_script_file=f"{cfg['cache_dir']}/{cfg['audio']['output_script_file']}",
)

get_post.generate_audio_transcript(
    source_audio_file=f"{cfg['cache_dir']}/{cfg['audio']['output_audio_file']}",
    source_text_file=f"{cfg['cache_dir']}/{cfg['audio']['output_script_file']}",
)

get_post.quit()

create_video = MoviepyCreateVideo(
    config_file=setup_file,
    speed_factor=1.0,
)

create_video(output_path="assets/output.mp4")

create_video.quit()

# Do not run the below when you are using shorts_maker within a container.

# ask_llm = AskLLM(config_file=setup_file)
# result = ask_llm.invoke(script)
# print(result["parsed"].title)
# print(result["parsed"].description)
# print(result["parsed"].tags)
# print(result["parsed"].thumbnail_description)
# ask_llm.quit_llm()

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

Generated from this post [here](https://www.reddit.com/r/selfhosted/comments/r2a6og/comment/hm5xoas/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button)

https://github.com/user-attachments/assets/6aad212a-bfd5-4161-a2bc-67d24a8de37f

## TODO
- [ ] Explain working and usage in blog.
- [x] Dockerize the project, To avoid the complex set up process.
- [x] Add option to fetch post from submission URLs.
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

This project is licensed under the GNU General Public License v3.0 License. See the [LICENSE](LICENSE) file for details.
