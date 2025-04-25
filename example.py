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
    # speed_factor=1.25,  # Set the speed factor for the video
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
