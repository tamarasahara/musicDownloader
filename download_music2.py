from yt_dlp import YoutubeDL
import os
import json
from datetime import date
import re
import datetime

MUSIC_FOLDER = "/home/maro/Documents/2_Areas/MusikDB/Music"
PLAYLIST_FILE = "/home/maro/Documents/2_Areas/MusikDB/playlists_to_download.txt"
VAULT_LOCATION=f"/home/maro/Documents/2_Areas/MusikDB"

DB_PATH = "/home/maro/Documents/1_Projekte/MusikDownloader/MediaDownloader/song_info.json"

ydl_opts = {
    "outtmpl": f"{MUSIC_FOLDER}/%(title)s.%(ext)s",
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "nooverwrites": True,
}

ydl = YoutubeDL(ydl_opts)

# ---------------------------
# DB LOAD / SAVE
# ---------------------------

def load_db():
    """Load JSON database or create empty structure."""
    if not os.path.exists(DB_PATH):
        return {"songs": []}

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"songs": []}
            return json.loads(content)
    except:
        print("WARNING: Could not read DB → resetting.")
        return {"songs": []}


def save_db(db):
    """Save DB to file."""
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


# ---------------------------
# MAIN FUNCTION
# ---------------------------

def extract_data_from_playlist_list(file_path):
    db = load_db()

    # Ensure structure exists
    if "songs" not in db:
        db["songs"] = []

    # Sets for fast lookup
    existing_video_urls = {s["video_url"] for s in db["songs"]}
    existing_playlist_urls = {s["playlist_url"] for s in db["songs"]}

    # Load playlist URLs from file
    with open(file_path, "r", encoding="utf-8") as f:
        playlists = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    print(f"Found {len(playlists)} playlists in file.")

    # Extract each playlist
    for playlist_url in playlists:
        print(f"→ Processing playlist: {playlist_url}")

        if playlist_url in existing_playlist_urls:
            print("  Skipping (already in DB).")
            continue

        playlist_info = ydl.extract_info(playlist_url, download=False)

        if playlist_info.get("_type") != "playlist":
            print("  Not a playlist. Skipping.")
            continue

        playlist_name = playlist_info.get("title")

        print(f"  Playlist name: {playlist_name}")
        print(f"  Contains {len(playlist_info['entries'])} videos.")

        # Extract each video
        for entry in playlist_info["entries"]:
            # Skip removed / private / unavailable videos
            if entry is None:
                continue

            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
            video_title = entry.get("title") or "Unknown Title"
            channel = entry.get("channel") or entry.get("uploader")
            upload_date = entry.get("upload_date")  # optional

            # Skip if already in DB
            if video_url in existing_video_urls:
                continue

            db["songs"].append({
                "playlist_url": playlist_url,
                "playlist_name": playlist_name,
                "video_url": video_url,
                "video_title": video_title,
                "channel": channel,
                "upload_date": upload_date,
                "file_path": None,
                "downloaded": False,
                "obsidian_note": False,
                "type": "song"
            })

    save_db(db)
    print("✔ Extraction complete.")

def mark_downloaded_files(folder_path):
    """
    folder_path: path to the folder containing your downloaded files
    Updates the JSON DB to mark songs as downloaded if the corresponding file exists.
    """
    db = load_db()
    files = os.listdir(folder_path)

    # Make a set of lowercase filenames for faster lookup
    file_set = {f.lower() for f in files}

    updated = 0

    for song in db.get("songs", []):
        if song.get("downloaded"):
            continue  # already marked

        # Use video_title to find matching file
        title = song.get("video_title", "")
        if not title:
            continue

        # build expected filename (as in your outtmpl)
        expected_files = [f"{title}.mp3", f"{title}.webm"]  # some safety for extension
        matched = None
        for ef in expected_files:
            if ef.lower() in file_set:
                matched = ef
                break

        if matched:
            song["file_path"] = os.path.join(folder_path, matched)
            song["downloaded"] = True
            updated += 1

    save_db(db)
    print(f"Marked {updated} songs as downloaded.")

def clean_title(title: str, channel_name: str | None) -> str:
    """
    Remove unwanted parts like (Official Video), [Official Audio],
    and channel name if provided.
    """
    import re

    # Remove (official video), [Official Audio], etc.
    title_clean = re.sub(r"[\(\[]\s*official\s*(video|audio)\s*[\)\]]", "", title, flags=re.IGNORECASE)

    return title_clean.strip()

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
    return True

def generate_obsidian_notes():
    """
    Go through the DB and create Obsidian notes for all downloaded songs that
    don't have a note yet.
    """
    db = load_db()
    count_created = 0

    for song in db.get("songs", []):
        if not song.get("downloaded", False):
            continue  # skip songs that aren't downloaded

        # if song.get("obsidian_note", False):
        #     continue  # skip songs that already have a note

        mp3_path = song.get("file_path")
        if not mp3_path or not os.path.exists(mp3_path):
            print(f"Skipping song, file missing: {song.get('video_title')}")
            continue

        album_title = song.get("playlist_name", "Unknown Album")
        upload_date = song.get("upload_date", "Unknown Date")
        channel_title = song.get("channel", "Unknown Artist")
        song_title = song.get("video_title", "Unknown Title")

        created = create_obsidian_file(song_title, channel_title, upload_date, album_title)
        if created:
            song["obsidian_note"] = True
            count_created += 1

    save_db(db)
    print(f"Obsidian note generation complete. Created {count_created} new notes.")

def add_type_to_song_notes():
    for filename in os.listdir(VAULT_LOCATION):
        if not filename.endswith(".md"):
            continue

        full_path = os.path.join(VAULT_LOCATION, filename)

        with open(full_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Check if file starts with YAML front matter
        if text.startswith("---"):
            parts = text.split("---", 2)  # ['', yaml, rest]
            if len(parts) < 3:
                continue

            yaml_block = parts[1].strip()

            # Check if type already exists
            if "type: music" in yaml_block:
                continue

            # Add the type field at the end of the YAML block
            new_yaml = yaml_block + "\ntype: song"
            new_text = "---\n" + new_yaml + "\n---" + parts[2]

        else:
            # No YAML at all: create one
            new_text = (
                    "---\n"
                    "type: music\n"
                    "---\n"
                    + text
            )

        # Write back updated text
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_text)

        print("Updated:", filename)

def rename_yaml():
    for filename in os.listdir(VAULT_LOCATION):
        if not filename.endswith(".md"):
            continue

        full_path = os.path.join(VAULT_LOCATION, filename)

        with open(full_path, "r", encoding="utf-8") as f:
            text = f.read()

        if "type: music" not in text:
            continue

        new_text = text.replace('album: "[[She wants revenge]]"', 'album: "[[She wants revenge - album]]"')

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_text)

        print("Fixed:", filename)

def update_date():
    # Matches: uploaded: 20230921   (with any amount of spaces)
    pattern = re.compile(r"(uploaded:\s*)(\d{8})")

    for filename in os.listdir(VAULT_LOCATION):
        if not filename.endswith(".md"):
            continue

        full_path = os.path.join(VAULT_LOCATION, filename)

        with open(full_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Find all matches inside the file
        matches = pattern.findall(text)
        if not matches:
            continue

        def replace(match):
            prefix = match.group(1)
            digits = match.group(2)
            # parse 20230921 → datetime object
            dt = datetime.strptime(digits, "%Y%m%d")
            formatted = dt.strftime("%Y-%m-%d")
            return prefix + formatted

        new_text = pattern.sub(replace, text)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_text)

        print("Converted:", filename)


#extract_data_from_playlist_list(PLAYLIST_FILE)
#mark_downloaded_files(MUSIC_FOLDER)
#generate_obsidian_notes()
#add_type_to_song_notes()
#rename_yaml()
#update_date()
