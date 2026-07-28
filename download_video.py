from yt_dlp import YoutubeDL

BASE_FOLDER = r"/home/maro/Documents/1_Projekte/pazifik_project"
DEMO_URL = "https://www.youtube.com/watch?v=B0R0cHIjZdE"

ydl_opts = {
    "outtmpl": f"{BASE_FOLDER}/bla|)s%(title)s.%(ext)s",
    "format": "bestvideo[protocol!=m3u8][protocol!=m3u8_native]+bestaudio[protocol!=m3u8][protocol!=m3u8_native]/best[protocol!=m3u8]",
    "merge_output_format": "mp4",
    "cookiesfrombrowser": ("firefox",),  # change to "chrome", "brave", etc. if needed
    "extractor_args": {"youtube": {"player_client": ["tv_embedded"]}},
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
    "quiet": False,
}

def download_video(url):
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        print("Download successful:", info.get("title"))

download_video(DEMO_URL)