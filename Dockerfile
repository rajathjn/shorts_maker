# Use a Python 3.12 base image
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.6.6 /uv /bin/

# Set environment variables
# Set this appropriately or leave empty if not using Discord
ENV DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxxxxx"

# Install ffmpeg and Java
# Install dependencies for moviepy
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends ffmpeg openjdk-17-jre locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    locale-gen C.UTF-8 && \
    /usr/sbin/update-locale LANG=C.UTF-8

ENV LC_ALL=C.UTF-8

# Set working directory
ADD . /shorts_maker

RUN cd /shorts_maker && \
    uv sync --frozen
