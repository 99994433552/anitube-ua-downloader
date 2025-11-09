# anitube-ua-downloader

🎬 Automated batch downloader for anime episodes from anitube.in.ua

## Features

- Download all episodes from anime series
- Interactive two-step selection: voice/dub → player
- Automatic file naming in Plex/Jellyfin format: `Name (Year) S01E01.mp4`
- Fast downloads using yt-dlp with aria2c acceleration
- Resume support (skips already downloaded episodes)
- Multiple player support (ASHDI, TRG, MOON, etc.)

## Requirements

- Python 3.12+
- yt-dlp
- aria2c (optional, for faster downloads)

## Installation

```bash
# Clone repository
cd aniloader

# Install dependencies with uv
uv sync

# Optional: install aria2c for faster downloads
brew install aria2  # macOS
# or
apt install aria2  # Linux
```

## Docker Usage

If you prefer not to install dependencies locally, you can use Docker:

### Build the image

```bash
docker build -t aniloader .
```

### Using docker run

**Important:** Use `-it` flags for interactive voice selection and `-v` to mount downloads directory.

```bash
# Basic usage (interactive voice/player selection)
docker run -it -v $(pwd)/downloads:/downloads aniloader https://anitube.in.ua/4110-lyudina-benzopila.html

# With voice selection (non-interactive)
docker run -v $(pwd)/downloads:/downloads aniloader https://anitube.in.ua/... --voice 3

# With verbose output
docker run -it -v $(pwd)/downloads:/downloads aniloader https://anitube.in.ua/... --verbose

# Custom download directory
docker run -it -v /path/to/your/downloads:/downloads aniloader https://anitube.in.ua/...
```

**Flags explanation:**
- `-it` - Interactive terminal (required for voice/player selection prompts)
- `-v $(pwd)/downloads:/downloads` - Mount local `./downloads` directory to save files to host machine

### Using docker compose (recommended)

Docker Compose automatically handles volume mounting and interactive mode.

```bash
# Basic usage (interactive voice/player selection)
docker compose run aniloader https://anitube.in.ua/4110-lyudina-benzopila.html

# With voice selection (skip interactive prompt)
docker compose run aniloader https://anitube.in.ua/... --voice 3

# With verbose output
docker compose run aniloader https://anitube.in.ua/... --verbose
```

**Note:** Downloaded files will automatically appear in the `./downloads` directory on your host machine.

## Usage

### Basic usage (interactive voice selection)

```bash
uv run python main.py https://anitube.in.ua/4110-lyudina-benzopila.html
```

### Specify voice/dub option

```bash
# Use voice option number from the list (1-based index)
uv run python main.py <URL> --voice 3
```

### Specify output directory

```bash
uv run python main.py <URL> --output ~/Downloads/Anime
```

### Disable aria2c acceleration

```bash
uv run python main.py <URL> --no-aria2c
```

### Verbose logging

```bash
uv run python main.py <URL> --verbose
```

## How it works

1. Fetches anime metadata from the provided URL
2. Retrieves available voice/dub options via AJAX
3. Prompts user to select voice (or uses `--voice` parameter)
4. Shows available players for selected voice
5. Prompts user to select player (or uses first by default)
6. Extracts m3u8 video URLs from player iframes
7. Downloads episodes using yt-dlp with optimizations
8. Automatically detects season number from title
9. Creates Jellyfin-compatible directory structure

## File naming

Episodes are saved in Jellyfin-recommended format with season folders:

```
Series Name/
├── Season 01/
│   ├── Series Name S01E01.mp4
│   └── Series Name S01E02.mp4
└── Season 03/
    ├── Series Name S03E01.mp4
    └── Series Name S03E02.mp4
```

**Season detection examples:**
- `Chainsaw Man` → Season 01 (default)
- `One Punch Man 3` → Season 03 (extracted from title)
- `Attack on Titan Season 4` → Season 04

## Troubleshooting

### 403 Forbidden error

The site uses Cloudflare protection. The scraper handles this automatically by:
- Using proper headers and cookies
- Maintaining session across requests

### No episodes found

Try selecting a different voice option. Some voices may have different player sources.

### Download fails

- Check internet connection
- Verify yt-dlp is installed: `yt-dlp --version`
- Try without aria2c: `--no-aria2c`

## Development

Project structure:

```
aniloader/
   main.py              # CLI entry point
   aniloader/
      models.py        # Pydantic data models
      scraper.py       # Web scraping and AJAX
      extractor.py     # m3u8 URL extraction
      downloader.py    # yt-dlp wrapper
   pyproject.toml       # Dependencies
```

## License

MIT
