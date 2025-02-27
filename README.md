# ShortsMaker

ShortsMaker is a Python package designed to facilitate the creation of engaging short videos or social media clips. It leverages a variety of external services and libraries to streamline the process of generating, processing, and uploading short content.

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [External Dependencies](#external-dependencies)
5. [Environment Variables](#environment-variables)
6. [Usage](#usage)
7. [Development](#development)
8. [License](#license)

## Features

- **Automated Content Creation:** Easily generate engaging short videos.
- **External Service Integration:** Seamlessly integrates with services like Discord for notifications.
- **GPU-Accelerated Processing:** Optional GPU support for faster processing using whisperx.
- **Modular Design:** Built with extensibility in mind.
- **In Development:** AskLLM AI agent, which helps in generating metadata for YouTube or image generation.
- **In Development:** Image Generation, GenerateImage class created for text2image generation. Note: This uses flux, Hence maybe resource intensive.

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

Use the [example-setup.yml](example.setup.yml) to look at the `setup.yml` configuration.
Below is a basic example to get you started with ShortsMaker:

```python
from ShortsMaker import MoviepyCreateVideo
from ShortsMaker import ShortsMaker
import yaml
from pathlib import Path

setup_file = "youtube_shorts_automation/setup.yml"
with open(setup_file) as f:
    cfg = yaml.safe_load(f)

get_post = ShortsMaker(setup_file)
get_post.get_reddit_post()
with open( Path(cfg["cache_dir"])/cfg["reddit_post_getter"]["record_file_txt"] ) as f:
    script = f.read()

get_post.generate_audio(script)
get_post.generate_audio_transcript(
    source_audio_file = f"{cfg['cache_dir']}/{cfg["audio"]["output_audio_file"]}",
    source_text_file = f"{cfg['cache_dir']}/{cfg["audio"]["output_script_file"]}",
)
get_post.quit()

create_video = MoviepyCreateVideo(config_file=setup_file)
create_video()
create_video.quit ()
```

For more detailed usage instructions, please refer to the in-code documentation or the [project wiki](https://example.com/ShortsMaker-wiki).

## Development

If you want to contribute to the project, please follow these steps:

1. **Set up the development environment:**
   - Ensure you have Python 3.12.8 and uv installed.
   - Clone the repository and install the development dependencies.

2. **Run the Tests:**
   - Tests are located in the `tests/` directory.
   - Run tests using:
   - Note: Tests require the setup.yml to be at the project root.

     ```bash
     pytest
     ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
