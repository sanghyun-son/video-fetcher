import logging
from pathlib import Path

import typer

from vfetcher.utils import create_progress, download_videos, filter_already_downloaded

logger = logging.getLogger(__name__)


def download(
    ids: Path = typer.Option(
        ...,
        "--ids",
        "-i",
        help="Path to a text file containing YouTube video IDs, one per line.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
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
    delay: float = typer.Option(
        2.0,
        "--delay",
        "-d",
        help="Base delay between downloads in seconds.",
    ),
    jitter: float = typer.Option(
        1.0,
        "--jitter",
        "-j",
        help="Random jitter range added to delay (0 to jitter seconds).",
    ),
):
    """
    Downloads YouTube videos from a list of IDs.
    """
    logger.info(f"Reading video IDs from: {ids}")
    logger.info(f"Output directory set to: {out}")

    out.mkdir(parents=True, exist_ok=True)

    video_ids = [vid.strip() for vid in ids.read_text().splitlines() if vid.strip()]
    logger.info(f"Found {len(video_ids)} video IDs to process.")

    video_urls_to_download, skipped_count = filter_already_downloaded(video_ids, out)

    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} videos that were already downloaded.")

    if not video_urls_to_download:
        logger.info("No new videos to download.")
        return

    logger.info(f"Proceeding to download {len(video_urls_to_download)} new videos.")

    with create_progress() as progress:
        result = download_videos(video_urls_to_download, out, progress, delay, jitter)

    logger.info(
        f"Done. Success: {result.success_count}, Failed: {result.failure_count}, Skipped: {skipped_count}"
    )
    if result.failed_urls:
        logger.warning("Failed URLs:")
        for url in result.failed_urls:
            logger.warning(f"  - {url}")
