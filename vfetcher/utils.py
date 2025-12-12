import logging
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def get_ydl_opts(output_dir: Path) -> dict[str, Any]:
    """Returns common yt-dlp options."""
    return {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(output_dir / "%(title)s-%(id)s.%(ext)s"),
        "noplaylist": True,
        "progress_hooks": [],
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
        "logger": logger,
    }


def extract_video_id(vid: str) -> str:
    """Extract YouTube video ID from a URL or return as-is if already an ID."""
    if not vid.startswith("http"):
        return vid

    parsed_url = urlparse(vid)
    if (
        parsed_url.hostname in ["www.youtube.com", "youtube.com"]
        and parsed_url.path == "/watch"
    ):
        query_params = parse_qs(parsed_url.query)
        return query_params.get("v", [vid])[0]
    elif parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    return vid


def get_downloaded_video_ids(output_dir: Path) -> set[str]:
    """
    Scans the output directory for already downloaded video files and extracts their IDs.
    """
    downloaded_ids = set()
    video_id_pattern = r"-([a-zA-Z0-9_-]{11})\."
    for file_path in output_dir.iterdir():
        if file_path.is_file():
            match = re.search(video_id_pattern, file_path.name)
            if match:
                downloaded_ids.add(match.group(1))
    return downloaded_ids


def filter_already_downloaded(
    video_ids: list[str], output_dir: Path
) -> tuple[list[str], int]:
    """Filter out already downloaded videos and return URLs to download."""
    downloaded_ids = get_downloaded_video_ids(output_dir)
    logger.info(f"Found {len(downloaded_ids)} videos already downloaded in {output_dir}.")

    video_urls_to_download = []
    skipped_count = 0

    for vid in video_ids:
        actual_id = extract_video_id(vid)
        if actual_id in downloaded_ids:
            logger.info(f"Skipping {vid} (ID: {actual_id}) as it is already downloaded.")
            skipped_count += 1
        else:
            if vid.startswith("http"):
                video_urls_to_download.append(vid)
            else:
                video_urls_to_download.append(f"https://www.youtube.com/watch?v={vid}")

    return video_urls_to_download, skipped_count


def create_progress() -> Progress:
    """Create a Rich progress bar instance."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )


@dataclass
class DownloadResult:
    """Result of a download operation."""

    success_count: int
    failure_count: int
    failed_urls: list[str]


def download_videos(
    video_urls: list[str],
    output_dir: Path,
    progress: Progress,
    delay: float = 2.0,
    jitter: float = 1.0,
) -> DownloadResult:
    """Download a list of videos with progress tracking.

    Args:
        video_urls: List of video URLs to download.
        output_dir: Directory to save downloaded videos.
        progress: Rich Progress instance for display.
        delay: Base delay between downloads in seconds.
        jitter: Random jitter range (0 to jitter) added to delay.

    Returns:
        DownloadResult with success/failure counts and failed URLs.
    """
    ydl_opts = get_ydl_opts(output_dir)
    current_task_id = None
    success_count = 0
    failed_urls: list[str] = []

    overall_task = progress.add_task(
        "[green]Downloading videos...", total=len(video_urls)
    )

    def download_progress_hook(d):
        nonlocal current_task_id
        if current_task_id is None:
            return
        if d["status"] == "downloading":
            if d.get("total_bytes"):
                progress.update(
                    current_task_id,
                    completed=d["downloaded_bytes"],
                    total=d["total_bytes"],
                )
            elif d.get("total_bytes_estimate"):
                progress.update(
                    current_task_id,
                    completed=d["downloaded_bytes"],
                    total=d["total_bytes_estimate"],
                )
        elif d["status"] == "finished":
            progress.update(
                current_task_id,
                completed=d.get("total_bytes") or d.get("total_bytes_estimate", 0),
                refresh=True,
            )

    ydl_opts["progress_hooks"].append(download_progress_hook)

    for i, video_url in enumerate(video_urls):
        current_task_id = progress.add_task(
            f"[cyan]Downloading {video_url}", start=False
        )
        try:
            with YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                ydl.download([video_url])
            success_count += 1
            progress.update(overall_task, advance=1)
            progress.remove_task(current_task_id)
        except Exception as e:
            logger.warning(f"Failed to download video {video_url}: {e}")
            failed_urls.append(video_url)
            progress.update(overall_task, advance=1)
            progress.remove_task(current_task_id)

        # Add delay with jitter between downloads (skip after last video)
        if i < len(video_urls) - 1:
            sleep_time = delay + random.uniform(0, jitter)
            logger.debug(f"Waiting {sleep_time:.1f}s before next download...")
            time.sleep(sleep_time)

    return DownloadResult(
        success_count=success_count,
        failure_count=len(failed_urls),
        failed_urls=failed_urls,
    )
