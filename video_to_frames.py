#!/usr/bin/env python3
"""
Video → Frames Extractor
Extracts frames from a video file at a configurable FPS.

Requires: ffmpeg installed on your system
  macOS:   brew install ffmpeg
  Ubuntu:  sudo apt install ffmpeg
  Windows: https://ffmpeg.org/download.html
"""

import argparse
import os
import subprocess
import sys


def check_ffmpeg():
    """Make sure ffmpeg is available."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌  ffmpeg not found. Please install it:")
        print("    macOS:   brew install ffmpeg")
        print("    Ubuntu:  sudo apt install ffmpeg")
        print("    Windows: https://ffmpeg.org/download.html")
        sys.exit(1)


def get_video_duration(video_path: str) -> float:
    """Return the duration of the video in seconds."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def time_to_seconds(t: str) -> float:
    """
    Convert a timestamp string to seconds.
    Accepts: '90', '1:30', '0:01:30', '1:30.5'
    """
    t = t.strip()
    parts = t.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        pass
    raise ValueError(f"Cannot parse timestamp: '{t}'")


def extract_frames(
    video_path: str,
    output_dir: str,
    fps: int = 24,
    start: str = None,
    end: str = None,
    fmt: str = "png",
    quality: int = 2,
):
    """
    Extract frames from a video.

    Args:
        video_path: Path to the input video file.
        output_dir: Folder to save frames into.
        fps:        Frames per second to extract (default 24).
        start:      Start timestamp, e.g. '0:30' or '30' (seconds). None = beginning.
        end:        End timestamp,   e.g. '1:00' or '60' (seconds). None = end of video.
        fmt:        Output image format: 'png' or 'jpg'.
        quality:    PNG compression (1–9, lower = better) or JPEG quality (1–31, lower = better).
    """
    if not os.path.isfile(video_path):
        print(f"❌  File not found: {video_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    duration = get_video_duration(video_path)
    start_sec = time_to_seconds(start) if start else 0.0
    end_sec   = time_to_seconds(end)   if end   else duration

    if duration > 0:
        clip_len = end_sec - start_sec
        est_frames = int(clip_len * fps)
        print(f"  Video duration : {duration:.1f}s")
        print(f"  Extracting     : {start_sec:.1f}s → {end_sec:.1f}s  ({clip_len:.1f}s)")
        print(f"  FPS            : {fps}")
        print(f"  Est. frames    : ~{est_frames}")
        print(f"  Output format  : {fmt.upper()}")
        print(f"  Output folder  : {output_dir}\n")

    # Build ffmpeg command
    cmd = ["ffmpeg", "-y"]

    # Seek before input for speed (fast seek)
    if start_sec > 0:
        cmd += ["-ss", str(start_sec)]

    cmd += ["-i", video_path]

    # Precise end trimming
    if end:
        cmd += ["-to", str(end_sec - start_sec)]

    # Frame rate filter
    cmd += ["-vf", f"fps={fps}"]

    # Format-specific quality
    if fmt == "jpg":
        cmd += ["-q:v", str(quality)]
        frame_pattern = os.path.join(output_dir, "frame_%06d.jpg")
    else:
        cmd += ["-compression_level", str(quality)]
        frame_pattern = os.path.join(output_dir, "frame_%06d.png")

    cmd += [frame_pattern]

    print("Running ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌  ffmpeg error:\n{result.stderr}")
        sys.exit(1)

    # Count output files
    saved = len([f for f in os.listdir(output_dir) if f.startswith("frame_")])
    print(f"\n✅  Done! {saved} frames saved to: {output_dir}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract frames from a video at a configurable FPS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All frames at 24 fps (default)
  python video_to_frames.py myvideo.mp4

  # Custom fps and output folder
  python video_to_frames.py myvideo.mp4 -fps 12 -o frames/

  # Only extract frames between 0:30 and 1:15
  python video_to_frames.py myvideo.mp4 --start 0:30 --end 1:15

  # Save as JPEG instead of PNG
  python video_to_frames.py myvideo.mp4 --format jpg
        """,
    )
    parser.add_argument("video",               help="Path to the input video file")
    parser.add_argument("-o", "--output",      default="frames", help="Output folder (default: frames/)")
    parser.add_argument("-fps", "--fps",       type=int, default=24, help="Frames per second to extract (default: 24)")
    parser.add_argument("--start",             default=None, help="Start time, e.g. '30', '0:30', '0:00:30'")
    parser.add_argument("--end",               default=None, help="End time,   e.g. '90', '1:30', '0:01:30'")
    parser.add_argument("--format",            choices=["png", "jpg"], default="png", help="Output image format (default: png)")
    parser.add_argument("--quality",           type=int, default=2, help="Quality: PNG 1-9 (default 2, lower=better) / JPG 1-31 (default 2)")
    return parser.parse_args()


def interactive_mode():
    """Fallback interactive prompts if no CLI args given."""
    print("═══════════════════════════════════")
    print("     Video → Frames Extractor      ")
    print("═══════════════════════════════════\n")

    video = input("Video file path: ").strip().strip('"').strip("'")
    output = input("Output folder [frames]: ").strip() or "frames"
    fps_str = input("Frames per second [24]: ").strip() or "24"
    start = input("Start time (blank = beginning), e.g. 0:30: ").strip() or None
    end   = input("End time   (blank = end of video), e.g. 1:30: ").strip() or None
    fmt   = input("Image format png/jpg [png]: ").strip().lower() or "png"

    return argparse.Namespace(
        video=video,
        output=output,
        fps=int(fps_str),
        start=start,
        end=end,
        format=fmt if fmt in ("png", "jpg") else "png",
        quality=2,
    )


if __name__ == "__main__":
    check_ffmpeg()

    args = parse_args() if len(sys.argv) > 1 else interactive_mode()

    extract_frames(
        video_path=args.video,
        output_dir=args.output,
        fps=args.fps,
        start=args.start,
        end=args.end,
        fmt=args.format,
        quality=args.quality,
    )