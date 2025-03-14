from pathlib import Path

import yaml

from ShortsMaker import MoviepyCreateVideo, ShortsMaker

setup_file = "setup.yml"

with open(setup_file) as f:
    cfg = yaml.safe_load(f)

get_post = ShortsMaker(setup_file)

get_post.get_reddit_post()

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
)

create_video()

create_video.quit()

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
