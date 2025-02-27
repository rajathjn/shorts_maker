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

get_post.generate_audio(script)

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
