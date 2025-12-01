import logging
from pathlib import Path
from typing import Any

import typer
from yt_dlp import YoutubeDL

from vfetcher.utils import create_progress, download_videos, filter_already_downloaded

logger = logging.getLogger(__name__)


def get_channel_video_urls(channel_url: str, limit: int | None = None) -> list[str]:
    """Fetch video URLs from a YouTube channel."""
    # Ensure we're fetching from the videos tab
    if not channel_url.endswith("/videos"):
        channel_url = channel_url.rstrip("/") + "/videos"

    ydl_opts: dict[str, Any] = {
        "extract_flat": "in_playlist",
        "quiet": True,
    }
    if limit:
        ydl_opts["playlistend"] = limit

    with YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
        info = ydl.extract_info(channel_url, download=False)
        if info is None:
            return []
        entries = info.get("entries", [])
        return [entry["url"] for entry in entries if entry and entry.get("url")]


def channel(
    url: str = typer.Option(
        ...,
        "--url",
        "-u",
        help="YouTube channel URL (e.g., https://www.youtube.com/@ChannelName).",
    ),
    out: Path = typer.Option(
        "outputs/default",
        "--out",
        "-o",
        help="The directory to save the downloaded videos.",
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        "-n",
        help="Limit to the last N videos. Downloads all videos if not specified.",
    ),
):
    """
    Downloads videos from a YouTube channel.
    """
    logger.info(f"Fetching videos from channel: {url}")
    logger.info(f"Output directory set to: {out}")
    if limit:
        logger.info(f"Limiting to last {limit} videos.")

    out.mkdir(parents=True, exist_ok=True)

    logger.info("Fetching video list from channel...")
    video_urls = get_channel_video_urls(url, limit)
    logger.info(f"Found {len(video_urls)} videos in channel.")

    if not video_urls:
        logger.warning("No videos found in channel.")
        return

    video_urls_to_download, skipped_count = filter_already_downloaded(video_urls, out)

    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} videos that were already downloaded.")

    if not video_urls_to_download:
        logger.info("All videos already downloaded.")
        return

    logger.info(f"Proceeding to download {len(video_urls_to_download)} new videos.")

    with create_progress() as progress:
        download_videos(video_urls_to_download, out, progress)

    logger.info("Done.")
