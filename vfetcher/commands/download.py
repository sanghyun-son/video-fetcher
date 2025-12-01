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

    logger.info(f"Proceeding to download {len(video_urls_to_download)} new videos.")

    with create_progress() as progress:
        download_videos(video_urls_to_download, out, progress)

    logger.info("Done.")
