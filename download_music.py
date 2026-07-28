from yt_dlp import YoutubeDL
import os
from datetime import date
import re

MUSIC_FOLDER = f"/home/maro/Documents/1_Projekte/mappe/videos"
VAULT_LOCATION=f"/home/maro/Documents/2_Areas/MusikDB"

MUSIC_FILE=f"/home/maro/Documents/1_Projekte/mappe/videos.txt"
PLAYLIST_FILE=f"/home/maro/Documents/2_Areas/MusikDB/playlists_to_download.txt"

DEMO_URL="https://www.youtube.com/watch?v=BwXq1luBdjw"
PLAYLIST_URL=f"https://www.youtube.com/watch?v=YISVENOMaB4&list=PLFvR2bZRQluwKcYtMsyEqBC3w-jx1HYyY"

DOWNLOAD=True

ydl_opts = {
        "outtmpl": f"{MUSIC_FOLDER}/%(title)s.%(ext)s",
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "nooverwrites": True,

}

ydl = YoutubeDL(ydl_opts)

def clean_title(title: str, channel_name) -> str:
    # Remove things like (official video), [Official Audio], etc.
    cleaned = re.sub(
        r"[\(\[]\s*official\s*(video|audio)\s*[\)\]]",
        "",
        title,
        flags=re.IGNORECASE
    )

    # Escape channel name so it cannot break the regex
    channel_pattern = re.escape(channel_name)

    # Remove channel/artist name from title
    cleaned = re.sub(
        channel_pattern,
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    # Remove double spaces leftover
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()

def create_obsidian_file(song_title, channel_title, upload_date, album_title):
    """
    Creates a markdown note in the Obsidian vault with metadata,
    links to channel and album, and embeds the mp3 file.
    """
    print ("trying to create obsidinfile")
    # Convert the mp3 filename to match yt-dlp output
    mp3_filename = f"{song_title}.mp3"
    mp3_path = os.path.join(MUSIC_FOLDER, mp3_filename)

    # Create Obsidian note path
    song_title_clean = clean_title(song_title, channel_title)
    md_filename = f"{song_title_clean.replace('/', '-')}.md"
    md_path = os.path.join(VAULT_LOCATION, md_filename)

    # Create relative path for Obsidian linking
    rel_mp3 = os.path.relpath(mp3_path, VAULT_LOCATION)

    # Markdown template
    file_text = f"""---
title: "{song_title}"
artist: "[[{channel_title.capitalize()}]]"
album: "[[{album_title}]]"
source: YouTube
date-note-creation: {date.today().isoformat()}
date-upload: {upload_date}
file: "{rel_mp3}"
---

<audio controls>
  <source src="{rel_mp3}" type="audio/mpeg">
</audio>
    """

    # Write the markdown file
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(file_text)

    print(f"Created Obsidian note: {md_path}")

def download_music_single_video(url, album_title=None, channel_title=None):
    info = ydl.extract_info(url, download=DOWNLOAD)

    # for playlists, has to give the channel title from the playlist info
    # for songs, channel is in info object
    if channel_title is None:
        channel_title = info["channel"]

    create_obsidian_file(info["title"], channel_title, info["upload_date"], album_title)

def download_music_from_link_list_file(file_path):
    if not os.path.exists(file_path):
        print("Error: file does not exist:", file_path)
        return
    with open(file_path, "r", encoding="utf-8") as f:
        urls = []
        for line in f.readlines():
            cleaned = line.strip()
            if cleaned == "":
                continue  # skip empty lines

            if cleaned.startswith("#"):
                continue  # skip comments

            urls.append(cleaned)

    print(f"Found {len(urls)} individual links in file.")
    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] Downloading: {url}")
        try:
            download_music_single_video(url)
        except Exception as e:
            print("Error:", e)

def download_playlist(url):
    # extract playlist info WITHOUT downloading first (this will print a bunch of stuff)
    playlist_info = ydl.extract_info(url, download=False)

    if playlist_info.get("_type") == "playlist":
        entries = playlist_info["entries"]
        print(f" → Contains {len(entries)} videos")
        for key in playlist_info:
            print(key)

        for idx, entry in enumerate(entries, start=1):
            video_url = entry["url"]
            album_title = playlist_info["title"]
            print(f"   [{idx}/{len(entries)}] Downloading {video_url}")
            print(playlist_info["channel"], " ", album_title)
            # try:
            #     download_music_single_video(video_url, album_title, playlist_info["channel"])
            # except Exception as e:
            #     print("Error:", e)
    else:
        print("URL was not a playlist — skipping.")

    info = ydl.extract_info(url, download=DOWNLOAD)
def download_from_playlists_file(file_path):
    if not os.path.exists(file_path):
        print("Error: file does not exist:", file_path)
        return

    with open(file_path, "r", encoding="utf-8") as f:
        playlists = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]

    print(f"Found {len(playlists)} playlists in file.")

    for i, playlist_url in enumerate(playlists, start=1):
        print(f"\nPlaylist {i}/{len(playlists)}: {playlist_url}")

        download_playlist(playlist_url)


#download_music_single_video("https://www.youtube.com/watch?v=5MX6_KKQRoQ")
download_playlist("https://www.youtube.com/playlist?list=PLNSqr7guzAjMZGo9YC5SF2xrXFzD92afC")
#download_music_from_link_list_file(MUSIC_FILE)