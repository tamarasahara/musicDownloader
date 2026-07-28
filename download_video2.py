#!/usr/bin/env python3
"""
YouTube Video Downloader
Requires: yt-dlp  →  pip install yt-dlp
"""

import subprocess
import sys


def install_ytdlp():
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        print("Installing yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"])


def download_video(url: str, output_dir: str = ".", quality: str = "best", browser: str = None):
    """
    Download a YouTube video.

    Args:
        url:        YouTube video URL
        output_dir: Folder to save the file (default: current directory)
        quality:    'best', 'worst', or a resolution like '720', '1080'
        browser:    Browser to pull cookies from: 'chrome', 'firefox', 'edge', etc.
    """
    import yt_dlp

    if quality == "best":
        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    elif quality == "worst":
        fmt = "worstvideo+worstaudio/worst"
    else:
        fmt = (
            f"bestvideo[height<={quality}][ext=mp4]"
            f"+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best"
        )

    ydl_opts = {
        "format": fmt,
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "merge_output_format": "mp4",
        # Use the Android client — avoids most 403s without needing cookies
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    }

    # Use browser cookies if specified (most reliable 403 fix)
    if browser:
        ydl_opts["cookiesfrombrowser"] = (browser,)
        print(f"  → Using cookies from {browser}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        print(f"\n✅  Downloaded: {info.get('title', 'video')}")


if __name__ == "__main__":
    install_ytdlp()

    url = input("Enter YouTube URL: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        sys.exit(1)

    output_dir = input("Save to folder [. for current directory]: ").strip() or "."

    print("Quality options: best | worst | 1080 | 720 | 480 | 360")
    quality = input("Choose quality [best]: ").strip() or "best"

    print("\nCookie source (fixes 403 errors):")
    print("  Options: chrome | firefox | edge | safari | brave | none")
    browser_input = input("Browser to use cookies from [none]: ").strip().lower() or "none"
    browser = None if browser_input == "none" else browser_input

    print(f"\nDownloading → {output_dir}/  (quality: {quality})\n")
    try:
        download_video(url, output_dir, quality, browser)
    except Exception as e:
        print(f"\n❌  Error: {e}")
        print("\n── Troubleshooting ───────────────────────────────────────────")
        print("1. Try selecting a browser for cookies (chrome / firefox / edge)")
        print("   Make sure you're logged into YouTube in that browser.")
        print("2. Update yt-dlp:  pip install -U yt-dlp")
        print("3. Some videos are region-locked or require a YouTube Premium account.")
        sys.exit(1)