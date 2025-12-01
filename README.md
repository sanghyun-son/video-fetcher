# Video Fetcher

A CLI tool to batch download YouTube videos.

## Installation

```bash
uv sync
```

## Usage

### Download from a list of video IDs

```bash
uv run -m vfetcher.main download -i ids.txt -o outputs/videos
```

Options:
- `-i, --ids` - Path to a text file containing YouTube video IDs or URLs (one per line)
- `-o, --out` - Output directory (default: `outputs/default`)

### Download from a channel

```bash
uv run -m vfetcher.main channel -u https://www.youtube.com/@ChannelName -o outputs/channel
```

Options:
- `-u, --url` - YouTube channel URL
- `-o, --out` - Output directory (default: `outputs/default`)
- `-n, --limit` - Limit to the last N videos (downloads all if not specified)

Examples:

```bash
# Download all videos from a channel
uv run -m vfetcher.main channel -u https://www.youtube.com/@JerryRigEverything -o outputs/jerry

# Download the last 10 videos
uv run -m vfetcher.main channel -u https://www.youtube.com/@JerryRigEverything -o outputs/jerry -n 10
```

## Features

- Skips already downloaded videos (detected by video ID in filename)
- Downloads in best quality up to 1080p MP4
- Progress bar with download speed and ETA
